"""Small client for the ChoreQuest Home Assistant API (/api/ha/state and /api/ha/act)."""
from __future__ import annotations

import asyncio
from typing import Any

import aiohttp


class ChoreQuestError(Exception):
    """The site answered with an error message we can show to the user."""


class CannotConnect(ChoreQuestError):
    """The site could not be reached."""


class InvalidAuth(ChoreQuestError):
    """The key was not accepted."""


class ChoreQuestApi:
    """Talks to one ChoreQuest site with one family key."""

    def __init__(self, session: aiohttp.ClientSession, url: str, key: str) -> None:
        self._session = session
        self._url = url.rstrip("/")
        self._key = key

    async def _call(self, method: str, path: str, payload: dict | None = None) -> dict[str, Any]:
        try:
            async with asyncio.timeout(15):
                resp = await self._session.request(
                    method,
                    self._url + path,
                    json=payload,
                    headers={"Authorization": f"Bearer {self._key}", "Accept": "application/json"},
                )
                try:
                    data = await resp.json(content_type=None)
                except (aiohttp.ContentTypeError, ValueError):
                    data = {}
        except (aiohttp.ClientError, TimeoutError) as err:
            raise CannotConnect(f"Could not reach {self._url}: {err}") from err
        if resp.status == 401:
            raise InvalidAuth((data or {}).get("error") or "The ChoreQuest key was not accepted.")
        if resp.status >= 400:
            raise ChoreQuestError((data or {}).get("error") or f"ChoreQuest answered {resp.status}.")
        if not isinstance(data, dict):
            raise ChoreQuestError("ChoreQuest sent an unexpected answer.")
        return data

    async def state(self) -> dict[str, Any]:
        """Today's lists for everyone in the family."""
        return await self._call("GET", "/api/ha/state")

    async def act(self, action: str, uid: str, **extra: Any) -> dict[str, Any]:
        """tick / untick / add / rename / delete a checklist task, or chore_done / chore_undo."""
        return await self._call("POST", "/api/ha/act", {"action": action, "uid": uid, **extra})
