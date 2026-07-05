import base64
import hashlib
import hmac
import time
import uuid

from aiohttp import ClientSession

from .const import API_URL


class SwitchBotAPI:

    def __init__(self, token, secret, device_id):
        self.token = token
        self.secret = secret
        self.device_id = device_id

    def _headers(self):

        timestamp = str(int(time.time() * 1000))
        nonce = str(uuid.uuid4())

        string_to_sign = self.token + timestamp + nonce

        sign = base64.b64encode(
            hmac.new(
                self.secret.encode(),
                string_to_sign.encode(),
                hashlib.sha256,
            ).digest()
        ).decode()

        return {
            "Authorization": self.token,
            "sign": sign,
            "t": timestamp,
            "nonce": nonce,
            "Content-Type": "application/json",
        }

    async def send_text(self, text):

        payload = {
            "command": "customPage",
            "parameter": text,
            "commandType": "command",
        }

        async with ClientSession() as session:

            async with session.post(
                API_URL.format(device_id=self.device_id),
                headers=self._headers(),
                json=payload,
            ) as response:

                return await response.json()