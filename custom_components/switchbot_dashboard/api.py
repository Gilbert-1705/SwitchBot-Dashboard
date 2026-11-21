import asyncio
import base64
import hashlib
import hmac
import logging
import time
import uuid

from aiohttp import ClientError, ClientSession, ClientTimeout

from .const import API_URL, MAX_PAYLOAD_BYTES
from .text import cap_bytes

_LOGGER = logging.getLogger(__name__)

# a hanging connection must not block the updater
REQUEST_TIMEOUT = 15

# statusCode of the result when the request never got an answer
# (no connection, DNS failure, timeout). Deliberately not None:
# a missing statusCode counts as success (see updater.send_succeeded).
NETWORK_ERROR = -1


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

        # Hard API limit: >300 bytes UTF-8 -> statusCode 190
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

        try:
            async with ClientSession(
                timeout=ClientTimeout(total=REQUEST_TIMEOUT)
            ) as session:

                async with session.post(
                    API_URL.format(device_id=self.device_id),
                    headers=self._headers(),
                    json=payload,
                ) as response:

                    result = await self._read_result(response)

        except (ClientError, asyncio.TimeoutError, TimeoutError) as err:
            # Internet down, DNS failure, SwitchBot not answering: a
            # normal failed result, so the updater retries later
            result = {
                "statusCode": NETWORK_ERROR,
                "message": f"{type(err).__name__}: {err}".rstrip(": "),
            }

        self._log_result(result)

        return result

    @staticmethod
    async def _read_result(response) -> dict:
        """Reads the API answer without ever raising on its format.

        On HTTP errors SwitchBot answers without a JSON body - most
        notably 429 (rate limit). ``response.json()`` would raise a
        ContentTypeError there, so those answers are mapped to a
        result dict carrying the HTTP status as ``statusCode``.
        """

        if response.status != 200:
            return {
                "statusCode": response.status,
                "message": f"HTTP {response.status}",
            }

        try:
            result = await response.json(content_type=None)
        except ValueError:
            return {
                "statusCode": response.status,
                "message": "invalid response body",
            }

        if not isinstance(result, dict):
            return {
                "statusCode": response.status,
                "message": "unexpected response body",
            }

        return result

    def _log_result(self, result):
        """Evaluates the SwitchBot status code (100 = OK)."""

        if not isinstance(result, dict):
            return

        status = result.get("statusCode")

        if status == 100 or status is None:
            return

        message = result.get("message", "")

        if status == NETWORK_ERROR:
            _LOGGER.warning(
                "SwitchBot API not reachable (%s) - the dashboard will "
                "retry later",
                message,
            )
        elif status == 429:
            _LOGGER.warning(
                "SwitchBot API rate limit hit (HTTP 429) - the "
                "dashboard will retry later"
            )
        elif status == 190:
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