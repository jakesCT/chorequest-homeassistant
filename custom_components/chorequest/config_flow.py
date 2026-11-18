"""Set up ChoreQuest with the site address and a family key."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_URL
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import CannotConnect, ChoreQuestApi, ChoreQuestError, InvalidAuth
from .const import CONF_KEY, DEFAULT_URL, DOMAIN


class ChoreQuestConfigFlow(ConfigFlow, domain=DOMAIN):
    """Ask for the site address and key, check them, and store them."""

    VERSION = 1

    async def _check(self, url: str, key: str) -> tuple[dict[str, Any] | None, str | None]:
        api = ChoreQuestApi(async_get_clientsession(self.hass), url, key)
        try:
            return await api.state(), None
        except InvalidAuth:
            return None, "invalid_auth"
        except CannotConnect:
            return None, "cannot_connect"
        except ChoreQuestError:
            return None, "unknown"

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            url = user_input[CONF_URL].strip().rstrip("/")
            if not url.startswith(("http://", "https://")):
                url = "https://" + url
            key = user_input[CONF_KEY].strip()
            state, err = await self._check(url, key)
            if err:
                errors["base"] = err
            else:
                await self.async_set_unique_id(state["family"]["id"])
                self._abort_if_unique_id_configured(updates={CONF_URL: url, CONF_KEY: key})
                return self.async_create_entry(title=f"{state['family']['name']} family", data={CONF_URL: url, CONF_KEY: key})
        schema = vol.Schema({vol.Required(CONF_URL, default=(user_input or {}).get(CONF_URL, DEFAULT_URL)): str, vol.Required(CONF_KEY): str})
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_reauth(self, entry_data: Mapping[str, Any]) -> ConfigFlowResult:
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        entry = self._get_reauth_entry()
        if user_input is not None:
            key = user_input[CONF_KEY].strip()
            state, err = await self._check(entry.data[CONF_URL], key)
            if err:
                errors["base"] = err
            elif state["family"]["id"] != entry.unique_id:
                errors["base"] = "wrong_family"
            else:
                return self.async_update_reload_and_abort(entry, data_updates={CONF_KEY: key})
        return self.async_show_form(step_id="reauth_confirm", data_schema=vol.Schema({vol.Required(CONF_KEY): str}), errors=errors)
