"""Polls ChoreQuest once a minute."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import ChoreQuestApi, ChoreQuestError, InvalidAuth
from .const import DOMAIN, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class ChoreQuestCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Holds the latest family state."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, api: ChoreQuestApi) -> None:
        super().__init__(hass, _LOGGER, config_entry=entry, name=DOMAIN, update_interval=SCAN_INTERVAL)
        self.api = api

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            return await self.api.state()
        except InvalidAuth as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except ChoreQuestError as err:
            raise UpdateFailed(str(err)) from err

    def member(self, uid: str) -> dict[str, Any] | None:
        """One family member from the latest data."""
        for m in (self.data or {}).get("members", []):
            if m["uid"] == uid:
                return m
        return None
