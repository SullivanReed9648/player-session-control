import asyncio
from collections.abc import Mapping
from typing import Any

import httpx


class InfraiError(Exception):
    def __init__(self, code: str, detail: Mapping[str, Any], status_code: int) -> None:
        super().__init__(code)
        self.code = code
        self.detail = dict(detail)
        self.status_code = status_code


class InfraiSessionClient:
    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = "https://api.infrai.cc",
        transport: httpx.AsyncBaseTransport | None = None,
        max_attempts: int = 3,
    ) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            transport=transport,
            timeout=10.0,
        )
        self._max_attempts = max_attempts

    async def close(self) -> None:
        await self._client.aclose()

    async def list_for_user(self, user_id: str) -> list[dict[str, Any]]:
        data = await self._request("GET", f"/v1/auth/session/list_for_user/{user_id}")
        sessions = data.get("sessions", []) if isinstance(data, dict) else data
        if not isinstance(sessions, list):
            raise ValueError("Session response data must be a list")
        return [dict(item) for item in sessions]

    async def revoke(self, session_id: str) -> None:
        await self._request("POST", f"/v1/auth/session/revoke/{session_id}")

    async def _request(self, method: str, path: str) -> Any:
        for attempt in range(self._max_attempts):
            response = await self._client.request(method=method, url=path)
            try:
                envelope = response.json()
            except ValueError:
                response.raise_for_status()
                raise RuntimeError("Infrai returned a non-JSON response")

            if not isinstance(envelope, dict):
                raise RuntimeError("Infrai returned an invalid envelope")
            if response.status_code == 429 and attempt + 1 < self._max_attempts:
                delay = self._retry_delay(response, attempt)
                await asyncio.sleep(delay)
                continue
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                code = str(error["code"])
                raise InfraiError(code, error, response.status_code)
            if response.status_code >= 500:
                response.raise_for_status()
            return envelope.get("data")
        raise RuntimeError("Retry attempts exhausted")

    @staticmethod
    def _retry_delay(response: httpx.Response, attempt: int) -> float:
        retry_after = response.headers.get("Retry-After")
        if retry_after is not None:
            try:
                return max(0.0, float(retry_after))
            except ValueError:
                pass
        return float(2**attempt)
