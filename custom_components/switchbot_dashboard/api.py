import base64
import hashlib
import hmac
import logging
import time
import uuid

from aiohttp import ClientSession

from .const import API_URL, MAX_PAYLOAD_BYTES
from .text import cap_bytes

_LOGGER = logging.getLogger(__name__)


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

        # Hartes API-Limit: >300 Bytes UTF-8 -> statusCode 190
        capped = cap_bytes(text, MAX_PAYLOAD_BYTES)

        if capped != text:
            _LOGGER.warning(
                "Payload exceeds %d bytes, truncated: %s",
                MAX_PAYLOAD_BYTES,
                capped,
            )

        payload = {
            "command": "customPage",
            "parameter": capped,
            "commandType": "command",
        }

        async with ClientSession() as session:

            async with session.post(
                API_URL.format(device_id=self.device_id),
                headers=self._headers(),
                json=payload,
            ) as response:

                result = await response.json()

        self._log_result(result)

        return result

    def _log_result(self, result):
        """Wertet den SwitchBot-Statuscode aus (100 = OK)."""

        if not isinstance(result, dict):
            return

        status = result.get("statusCode")

        if status == 100 or status is None:
            return

        message = result.get("message", "")

        if status == 190:
            _LOGGER.error(
                "SwitchBot API rejected the payload (statusCode 190, "
                "'%s') - text too long (>300 bytes UTF-8)",
                message,
            )
        else:
            _LOGGER.warning(
                "SwitchBot API returned statusCode %s: %s",
                status,
                message,
            )