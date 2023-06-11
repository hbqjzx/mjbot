import asyncio
import base64
import logging
import random
import time
import traceback
import urllib.parse
from enum import Enum
from typing import Optional

from wechaty import Wechaty, WechatyOptions, Contact, Message, Room
from wechaty_puppet import ScanStatus, FileBox, EventErrorPayload

from src import Config, id_generator, img_compress
from src.translate import ZhiShuYunGPTTranslator
from src.zsy_midjourney import ZhiShuYunMidjourney

log = logging.getLogger(__name__)


class Command(Enum):
    help = "help"
    generate = "mj"
    upsample = "upsample"
    variation = "variation"
    upsample_light = "upsample_light"
    upsample_beta = "upsample_beta"


action_commands = {Command.generate, Command.upsample, Command.variation, Command.upsample_light, Command.upsample_beta}

short2command = {
    "u": Command.upsample,
    "v": Command.variation,
}

command2short = {
    Command.upsample: "u",
    Command.variation: "v",
}

short2comment = {
    "u": "进行放大",
    "v": "进行变换",
}

tip1 = "✅绘制成功"
tip2 = "📎任务ID:"


class MidjourneyBot(Wechaty):
    def __init__(self, config: Config):
        super().__init__(WechatyOptions(puppet=config.wechaty_puppet))
        logging.basicConfig(level=logging.getLevelName(config.log_level.upper()))
        self.bot_name = None
        self._translator = ZhiShuYunGPTTranslator(config.zhishuyun_chatgpt_35_token)
        self._midjourney = ZhiShuYunMidjourney(config.zhishuyun_midjourney_token)

    async def on_scan(self, qr_code: str, status: ScanStatus, data: Optional[str] = None) -> None:
        if status == ScanStatus.Waiting and qr_code is not None:
            url = f"https://wechaty.js.org/qrcode/{urllib.parse.quote(qr_code, safe='')}"
            log.info(f"Scan QR Code to login: {status}\n{url}")
        else:
            log.info(f"Scan status {status}, {data}")

    async def on_login(self, contact: Contact) -> None:
        self.bot_name = contact.name
        log.info(f"User {self.bot_name} has logged in")

    async def on_logout(self, contact: Contact) -> None:
        log.info(f"User {self.bot_name} has logged out")
        self.bot_name = None

    async def on_error(self, payload: EventErrorPayload) -> None:
        log.error(f"Got error with [{type(payload)}] {payload}")

    async def on_message(self, msg: Message) -> None:
        room = msg.room()
        if room is None:
            return
        text = msg.text().strip()
        text, quote_from, quote_content = self.parse_quote(text)

        if not text.startswith(f"@{self.bot_name}"):
            return
        command_text = text[len(self.bot_name) + 1:].strip()
        if not command_text.startswith("/"):
            return
        command, args_text = self.split_first(command_text[1:], " ")
        if command is None or args_text is None:
            command = command_text[1:]
            args_text = ""

        command_idx = None
        try:
            command = Command(command)
        except ValueError:
            try:
                command, command_idx = short2command.get(command[:-1]), int(command[-1])
            except ValueError:
                return
            if command is None:
                return

        image_id = None
        if quote_from is not None:
            if quote_from != self.bot_name:
                return
            if not quote_content.startswith("@"):
                return
            at_some, response = self.split_first(quote_content, " ")
            if at_some is None or response is None or len(at_some) < 2:
                return
            quote_lines = response.splitlines()
            if len(quote_lines) < 2 or not quote_lines[0].strip().startswith(tip1) or \
                    not quote_lines[1].strip().startswith(tip2):
                return
            _, quote_job_id = self.split_first(quote_lines[1], ":")
            if quote_job_id is None:
                return
            image_id = id_generator.decode(quote_job_id)
            if image_id is None:
                return

        from_contact = msg.talker()

        if command == Command.help:
            await self.command_help(room, from_contact)
            return

        if command in action_commands:
            if command == Command.generate:
                if len(args_text) == 0:
                    await self.command_help(room, from_contact)
                    return
                await asyncio.sleep(1)
                await room.say(f"🚀绘制任务已提交，请稍等\nPrompt: {args_text}", mention_ids=[from_contact.contact_id])
                action_str = command.name
            else:
                if image_id is None or command_idx is None:
                    return
                await asyncio.sleep(1)
                await room.say(f"🚀绘制任务已提交，请稍等\nReal Command: /{command.value}{command_idx}",
                               mention_ids=[from_contact.contact_id])
                action_str = f"{command.name}{command_idx}"
            _start = time.time()
            translated = None
            if command == Command.generate:
                status, translated = await self._translator.run1(args_text)
                if not status:
                    if 400 <= translated < 500:
                        await self.error_4xx(room, from_contact)
                        return
                    if 500 <= translated:
                        await self.error_5xx(room, from_contact)
                        return
                    return
                log.info(f"Translated from [{args_text}] 2 [{translated}]")
                if time.time() - _start > 8:
                    await room.say("⏳仍在继续生成中...", mention_ids=[from_contact.contact_id])
            status, response = await self._midjourney.run1(action_str, translated, image_id)
            if not status:
                if 400 <= response < 500:
                    await self.error_4xx(room, from_contact)
                    return
                if 500 <= response:
                    await self.error_5xx(room, from_contact)
                    return
                return
            _end = time.time()
            await room.say("⏳生成结束，正在下载、压缩、上传图片...", mention_ids=[from_contact.contact_id])
            await self.send_image(response, room)
            job_id = id_generator.encode(str(response['image_id']))
            if command == Command.generate:
                await room.say(
                    f"{tip1}（{int(_end - _start)}秒）\n{tip2} {job_id}\n原图片地址: {response['image_url']}\nPrompt: {args_text}\nReal Prompt: {translated}\n\n{self.parse_commands(response['actions'], job_id)}",
                    mention_ids=[from_contact.contact_id])
            else:
                await room.say(
                    f"{tip1}（{int(_end - _start)}秒）\n{tip2} {job_id}\n原图片地址: {response['image_url']}\nReal Command: /{command.value}{command_idx}\n\n{self.parse_commands(response['actions'], job_id)}",
                    mention_ids=[from_contact.contact_id])

    @staticmethod
    async def send_image(response, room: Room):
        try:
            pic_bytes = await img_compress.compress_from_url1(response["image_url"])
            fb = FileBox.from_base64(base64=base64.b64encode(pic_bytes), name="IMAGE.png")
            await room.say(fb)
        except:
            log.error(f"send image fail\n{traceback.format_exc()}")
            await room.say(f"⭕图片下载失败，请直接访问原链接: {response['image_url']}")

    @staticmethod
    async def command_help(room: Room, from_contact: Contact):
        await room.say(f"💡@ 我并输入 {Command.generate.value} 命令生成图片，如：\n/{Command.generate.value} 一只白猫",
                       mention_ids=[from_contact.contact_id])

    @staticmethod
    async def error_4xx(room: Room, from_contact: Contact):
        await room.say(f"⭕当前服务配置不正确，请联系管理员处理", mention_ids=[from_contact.contact_id])

    @staticmethod
    async def error_5xx(room: Room, from_contact: Contact):
        await room.say(f"⭕Midjourney未正确返回结果或超时，请重试或联系管理员处理", mention_ids=[from_contact.contact_id])

    @staticmethod
    def parse_commands(actions, job_id):
        all_shorts = set()
        command_count = dict()
        for action in actions:
            if len(action) < 2:
                continue
            try:
                command, idx = Command(action[:-1]), int(action[-1])
            except ValueError:
                continue
            if command not in command2short:
                continue
            all_shorts.add(command2short[command])
            if command not in command_count:
                command_count[command2short[command]] = set()
            command_count[command2short[command]].add(idx)
        if len(all_shorts) == 0:
            return ""
        tips = "💡继续生成图片, @ 我并**引用**此消息，支持以下命令:\n"
        for sc in all_shorts:
            tips += "- /%s{图片编号} %s\n" % (sc, short2comment[sc])
        tips += "例如:\n"
        for cmd, idxs in command_count.items():
            tips += f"/{cmd}{random.choice(list(idxs))}\n"
        return tips.strip()

    @staticmethod
    def parse_quote(text: str):
        quote_all, left = MidjourneyBot.split_first(text, "\n- -")
        if quote_all is None or left is None:
            return text, None, None
        left, new_text = MidjourneyBot.split_first(left, "- -\n")
        if left is None or new_text is None:
            return text, None, None
        if len(left) > 0:
            for ci, cc in enumerate(left):
                if ci % 2 == 0:
                    if cc != "-":
                        return text, None, None
                else:
                    if cc != " ":
                        return text, None, None
        if quote_all.startswith('"') or quote_all.startswith("「"):
            quote_all = quote_all[1:]
        if quote_all.endswith('"') or quote_all.endswith("」"):
            quote_all = quote_all[:-1]
        quote_from, quote_context = MidjourneyBot.split_first(quote_all.replace("：", ":"), ":")
        if quote_from is None or quote_context is None:
            return text, None, None
        return new_text, quote_from, quote_context

    @staticmethod
    def split_first(text: str, s: str):
        idx = text.find(s)
        if idx < 0:
            return None, None
        return text[0:idx].strip(), text[idx + len(s):].strip()
