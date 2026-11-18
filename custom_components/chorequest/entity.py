"""Shared base: one Home Assistant device per family member."""
from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ChoreQuestCoordinator


class ChoreQuestEntity(CoordinatorEntity[ChoreQuestCoordinator]):
    """An entity that belongs to one family member."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: ChoreQuestCoordinator, uid: str, key: str) -> None:
        super().__init__(coordinator)
        self.uid = uid
        fam = coordinator.data["family"]
        m = coordinator.member(uid) or {}
        self._attr_unique_id = f"{fam['id']}_{uid}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{fam['id']}_{uid}")},
            name=m.get("name", "Family member"),
            manufacturer="ChoreQuest",
            model="Parent" if m.get("role") == "adult" else "Kid",
            configuration_url=str(coordinator.api._url),  # noqa: SLF001
        )

    @property
    def member(self) -> dict[str, Any]:
        return self.coordinator.member(self.uid) or {}

    @property
    def available(self) -> bool:
        return super().available and self.coordinator.member(self.uid) is not None
