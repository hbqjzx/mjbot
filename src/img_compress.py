import io

import aiohttp
import math
import requests
from PIL import Image


def _compute_scale(src_width, src_height):
    src_width = src_width + 1 if src_width % 2 == 1 else src_width
    src_height = src_height + 1 if src_height % 2 == 1 else src_height

    long_side = max(src_width, src_height)
    short_side = min(src_width, src_height)

    scale = short_side / long_side
    if 1 >= scale > 0.5625:
        if long_side < 1664:
            return 1
        elif long_side < 4990:
            return 2
        elif 4990 < long_side < 10240:
            return 4
        else:
            return max(1, long_side // 1280)
    elif 0.5625 >= scale > 0.5:
        return max(1, long_side // 1280)
    else:
        return math.ceil(long_side / (1280.0 / scale))


def _simple_format(img):
    if img.mode == "RGBA":
        return img, "PNG"
    elif img.mode == "RGB":
        return img, "JPEG"
    else:
        return img.convert("RGB"), "JPEG"


def compress(img):
    _img, _format = _simple_format(img)
    src_width, src_height = _img.size
    scale = _compute_scale(src_width, src_height)
    new_img = _img.resize((src_width // scale, src_height // scale), Image.LANCZOS)
    new_bs = io.BytesIO()
    new_img.save(new_bs, format=_format, quality=60)
    return new_bs.getvalue()


def compress_from_url(url):
    resp = requests.get(url, timeout=60)
    if resp.status_code == 200:
        return compress(Image.open(io.BytesIO(resp.content)))
    else:
        raise ValueError(f"[{resp.status_code}] {resp.text}")


async def compress_from_url1(url):
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=300)) as session:
        async with session.get(url=url) as resp:
            if resp.status == 200:
                resp_bs = await resp.read()
                return compress(Image.open(io.BytesIO(resp_bs)))
            else:
                resp_text = await resp.text()
                raise ValueError(f"[{resp.status}] {resp_text}")
