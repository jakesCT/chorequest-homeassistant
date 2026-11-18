"""Per-person sensors: tasks left, chores left, coins, streak and level."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription, SensorStateClass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import ChoreQuestConfigEntry
from .entity import ChoreQuestEntity


def _tasks_left(m: dict[str, Any]) -> list[dict[str, Any]]:
    return [t for t in m.get("tasks", []) if not t["done"]]


def _chores_left(m: dict[str, Any]) -> list[dict[str, Any]]:
    # up-for-grabs chores nobody has grabbed yet are optional, so they don't count
    return [c for c in m.get("chores", []) if c["state"] in ("todo", "rejected") and c.get("mine", True)]


@dataclass(frozen=True, kw_only=True)
class CQSensor(SensorEntityDescription):
    value: Callable[[dict[str, Any]], Any]
    attrs: Callable[[dict[str, Any]], dict[str, Any]] | None = None


SENSORS = (
    CQSensor(key="tasks_left", name="Tasks left", icon="mdi:clipboard-list-outline", state_class=SensorStateClass.MEASUREMENT,
             value=lambda m: len(_tasks_left(m)),
             attrs=lambda m: {"tasks": [t["title"] for t in _tasks_left(m)], "later_today": (m.get("later") or {}).get("count", 0), "next_at": (m.get("later") or {}).get("next")}),
    CQSensor(key="chores_left", name="Chores left", icon="mdi:broom", state_class=SensorStateClass.MEASUREMENT,
             value=lambda m: len(_chores_left(m)),
             attrs=lambda m: {"chores": [c["title"] for c in _chores_left(m)], "waiting_for_ok": [c["title"] for c in m.get("chores", []) if c["state"] == "pending"]}),
    CQSensor(key="coins", name="Coins", icon="mdi:hand-coin-outline", state_class=SensorStateClass.MEASUREMENT, value=lambda m: m.get("coins")),
    CQSensor(key="streak", name="Streak", icon="mdi:fire", native_unit_of_measurement="days", state_class=SensorStateClass.MEASUREMENT, value=lambda m: m.get("streak")),
    CQSensor(key="level", name="Level", icon="mdi:star-circle-outline", value=lambda m: m.get("level"), attrs=lambda m: {"title": m.get("title"), "xp": m.get("xp")}),
)


async def async_setup_entry(hass: HomeAssistant, entry: ChoreQuestConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    c = entry.runtime_data
    async_add_entities(CQSensorEntity(c, m["uid"], d) for m in c.data["members"] for d in SENSORS)


class CQSensorEntity(ChoreQuestEntity, SensorEntity):
    entity_description: CQSensor

    def __init__(self, coordinator, uid: str, description: CQSensor) -> None:
        super().__init__(coordinator, uid, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> Any:
        return self.entity_description.value(self.member)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        f = self.entity_description.attrs
        return f(self.member) if f else None
