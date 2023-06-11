import logging
import traceback
from functools import lru_cache

import aiohttp
import requests

log = logging.getLogger(__name__)


class Translator:
    def run(self, prompt):
        pass

    async def run1(self, prompt):
        pass


class GPTTranslator(Translator):
    def __init__(self):
        self._gpt_prompt = """我希望你能担任英语翻译、拼写校对和修辞改进的角色。我会将翻译的结果用于如stable diffusion、midjourney等生成图片，所以请确保意思不变，但更适合此类场景。我会用任何语言和你交流，你会识别语言，将其翻译为英语并仅回答翻译的最终结果，不要写解释。我的第一句话是："{}"。请立刻翻译，不要回复其它内容。"""

    def _generate_question(self, prompt):
        return self._gpt_prompt.format(prompt)


class ZhiShuYunGPTTranslator(GPTTranslator):
    def __init__(self, token):
        super().__init__()
        self._url = "https://api.zhishuyun.com/chatgpt"
        self._session = requests.Session()
        self._params = {"token": token}
        self._session.params = self._params
        self._headers = {
            "accept": "application/json",
            "content-type": "application/json"
        }
        self._session.headers.update(**self._headers)

    async def run1(self, prompt):
        try:
            async with aiohttp.ClientSession(headers=self._headers,
                                             timeout=aiohttp.ClientTimeout(total=600)) as session:
                async with session.post(url=self._url, params=self._params,
                                        json={"question": self._generate_question(prompt), "stateful": False,
                                              "timeout": 600}) as resp:
                    resp_status_code = resp.status
                    if resp_status_code == 200:
                        resp_json = await resp.json()
                        return True, self._clean_answer(resp_json["answer"])
                    resp_text = await resp.text()
                    log.error(f"ZhiShuYunGPTTranslator response with [{resp_status_code}] {resp_text}")
                    return False, resp_status_code
        except:
            log.error(f"ZhiShuYunGPTTranslator request with exception\n{traceback.format_exc()}")
            return False, 600

    @lru_cache(maxsize=1024)
    def run(self, prompt):
        try:
            log.debug(f"ZhiShuYunGPTTranslator start: {prompt}")
            res = self._session.post(url=self._url, json={
                "question": self._generate_question(prompt),
                "stateful": False,
                "timeout": 600
            }, timeout=600)
            if res.status_code == 200:
                log.debug(f"ZhiShuYunGPTTranslator success: {prompt}")
                return True, self._clean_answer(res.json()["answer"])
            log.error(f"ZhiShuYunGPTTranslator response with [{res.status_code}] {res.text}")
            return False, res.status_code
        except:
            log.error(f"ZhiShuYunGPTTranslator request with exception\n{traceback.format_exc()}")
            return False, 600

    @staticmethod
    def _clean_answer(answer):
        _answer = answer
        if _answer.startswith('"'):
            _answer = _answer[1:]
        if _answer.endswith('"'):
            _answer = _answer[:-1]
        if _answer.endswith("."):
            _answer = _answer[:-1]
        return _answer
