"""ChoreQuest: today's checklists and chores as Home Assistant to-do lists."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_URL, Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import ChoreQuestApi
from .const import CONF_KEY
from .coordinator import ChoreQuestCoordinator

PLATFORMS = [Platform.TODO, Platform.SENSOR]

type ChoreQuestConfigEntry = ConfigEntry[ChoreQuestCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: ChoreQuestConfigEntry) -> bool:
    api = ChoreQuestApi(async_get_clientsession(hass), entry.data[CONF_URL], entry.data[CONF_KEY])
    coordinator = ChoreQuestCoordinator(hass, entry, api)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    members = {m["uid"] for m in coordinator.data["members"]}

    @callback
    def _members_changed() -> None:
        # someone joined or left the family: reload so their lists appear / disappear
        if coordinator.data and {m["uid"] for m in coordinator.data["members"]} != members:
            hass.config_entries.async_schedule_reload(entry.entry_id)

    entry.async_on_unload(coordinator.async_add_listener(_members_changed))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ChoreQuestConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
