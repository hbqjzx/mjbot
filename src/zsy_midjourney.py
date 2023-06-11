import logging
import traceback

import aiohttp
import requests

log = logging.getLogger(__name__)


class ZhiShuYunMidjourney:
    def __init__(self, token):
        self._url = "https://api.zhishuyun.com/midjourney/imagine"
        self._session = requests.Session()
        self._params = {"token": token}
        self._session.params = self._params
        self._headers = {
            "accept": "application/json",
            "content-type": "application/json"
        }
        self._session.headers.update(**self._headers)

    async def run1(self, action, prompt, image_id=None):
        try:
            async with aiohttp.ClientSession(headers=self._headers,
                                             timeout=aiohttp.ClientTimeout(total=600)) as session:
                async with session.post(url=self._url, params=self._params,
                                        json={"action": action, "prompt": prompt, "image_id": image_id,
                                              "timeout": 600}) as resp:
                    resp_status_code = resp.status
                    if resp_status_code == 200:
                        resp_json = await resp.json()
                        return True, resp_json
                    resp_text = await resp.text()
                    log.error(f"ZhiShuYunMidjourney response with [{resp_status_code}] {resp_text}")
                    return False, resp_status_code
        except:
            log.error(f"ZhiShuYunMidjourney request with exception\n{traceback.format_exc()}")
            return False, 600

    def run(self, action, prompt, image_id=None):
        try:
            res = self._session.post(url=self._url, json={
                "action": action,
                "prompt": prompt,
                "image_id": image_id,
                "timeout": 600
            }, timeout=600)
            if res.status_code == 200:
                return True, res.json()
            log.error(f"ZhiShuYunMidjourney response with [{res.status_code}] {res.text}")
            return False, res.status_code
        except:
            log.error(f"ZhiShuYunMidjourney request with exception\n{traceback.format_exc()}")
            return False, 600
