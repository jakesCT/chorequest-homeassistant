"""Two to-do lists per family member: today's checklist (fully editable) and today's chores (tick only)."""
from __future__ import annotations

import re
from datetime import date, datetime, time
from typing import Any
from zoneinfo import ZoneInfo

from homeassistant.components.todo import TodoItem, TodoItemStatus, TodoListEntity, TodoListEntityFeature
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import ChoreQuestConfigEntry
from .api import ChoreQuestError
from .coordinator import ChoreQuestCoordinator
from .entity import ChoreQuestEntity


async def async_setup_entry(hass: HomeAssistant, entry: ChoreQuestConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    c = entry.runtime_data
    ents: list[TodoListEntity] = []
    for m in c.data["members"]:
        ents += [ChecklistTodo(c, m["uid"]), ChoresTodo(c, m["uid"])]
    async_add_entities(ents)


def _fmt(hhmm: str) -> str:
    h, m = (int(x) for x in hhmm.split(":"))
    return f"{(h % 12) or 12}{':%02d' % m if m else ''} {'AM' if h < 12 else 'PM'}"


class _Base(ChoreQuestEntity, TodoListEntity):
    async def _act(self, action: str, **extra: Any) -> None:
        try:
            await self.coordinator.api.act(action, self.uid, **extra)
        except ChoreQuestError as err:
            raise HomeAssistantError(str(err)) from err
        finally:
            await self.coordinator.async_refresh()

    def _find(self, key: str, uid: str | None) -> dict[str, Any] | None:
        return next((x for x in self.member.get(key, []) if x["id"] == uid), None)


class ChecklistTodo(_Base):
    """Checklist tasks that are on right now (plus any missed earlier today). Add, rename, tick and delete sync both ways."""

    _attr_name = "Checklist"
    _attr_icon = "mdi:clipboard-check-outline"
    _attr_supported_features = TodoListEntityFeature.CREATE_TODO_ITEM | TodoListEntityFeature.UPDATE_TODO_ITEM | TodoListEntityFeature.DELETE_TODO_ITEM

    def __init__(self, coordinator: ChoreQuestCoordinator, uid: str) -> None:
        super().__init__(coordinator, uid, "checklist")

    @property
    def todo_items(self) -> list[TodoItem]:
        fam = self.coordinator.data["family"]
        tz, day = ZoneInfo(fam["tz"]), date.fromisoformat(fam["day"])
        items = []
        for t in self.member.get("tasks", []):
            all_day = t["start"] == "00:00" and t["end"] >= "23:59"
            h, m = (int(x) for x in t["end"].split(":"))
            items.append(TodoItem(
                uid=t["id"],
                summary=f"{t['icon']} {t['title']}".strip(),
                status=TodoItemStatus.COMPLETED if t["done"] else TodoItemStatus.NEEDS_ACTION,
                due=None if all_day else datetime.combine(day, time(h, m), tzinfo=tz),
                description=("Missed: was due by " + _fmt(t["end"])) if t.get("missed") else (None if all_day else "Until " + _fmt(t["end"])),
            ))
        return items

    def _plain(self, summary: str, icon: str) -> str:
        s = (summary or "").strip()
        return s[len(icon):].strip() if icon and s.startswith(icon) else s

    async def async_create_todo_item(self, item: TodoItem) -> None:
        await self._act("add", title=(item.summary or "").strip())

    async def async_update_todo_item(self, item: TodoItem) -> None:
        t = self._find("tasks", item.uid)
        if t is None:
            raise HomeAssistantError("That task is not on the list any more.")
        new = self._plain(item.summary or "", t["icon"])
        if new and new != t["title"]:
            await self._act("rename", id=t["id"], title=new)
        done = item.status == TodoItemStatus.COMPLETED
        if done != t["done"]:
            await self._act("tick" if done else "untick", id=t["id"])

    async def async_delete_todo_items(self, uids: list[str]) -> None:
        for uid in uids:
            await self._act("delete", id=uid)


class ChoresTodo(_Base):
    """Today's chores. Tick to mark done (approvals still apply); untick to undo. Chores are created and edited on the website."""

    _attr_name = "Chores"
    _attr_icon = "mdi:broom"
    _attr_supported_features = TodoListEntityFeature.UPDATE_TODO_ITEM

    def __init__(self, coordinator: ChoreQuestCoordinator, uid: str) -> None:
        super().__init__(coordinator, uid, "chores")

    @property
    def todo_items(self) -> list[TodoItem]:
        cur = self.coordinator.data["family"].get("cur", "$")
        items = []
        for c in self.member.get("chores", []):
            worth = f"{cur}{c['cash'] / 100:.2f}".replace(".00", "") if c.get("cash") else f"{c['points']} points"
            note = {"pending": " · waiting for a parent’s OK", "rejected": " · sent back, try again"}.get(c["state"], "")
            if c.get("overdue"):
                note += " · overdue"
            if c.get("note") and c["state"] == "todo":
                note += " · " + c["note"]
            due = datetime.fromtimestamp(c["claimDue"] / 1000, tz=ZoneInfo(self.coordinator.data["family"]["tz"])) if c.get("claimDue") and c["state"] == "todo" else None
            items.append(TodoItem(
                uid=c["id"],
                summary=f"{c['icon']} {c['title']}".strip(),
                status=TodoItemStatus.COMPLETED if c["state"] in ("done", "pending") else TodoItemStatus.NEEDS_ACTION,
                description=worth + note,
                due=due,
            ))
        return items

    async def async_update_todo_item(self, item: TodoItem) -> None:
        c = self._find("chores", item.uid)
        if c is None:
            raise HomeAssistantError("That chore is not on today’s list any more.")
        if (item.summary or "").strip() != f"{c['icon']} {c['title']}".strip():
            raise HomeAssistantError("Chores can only be ticked here. Change them on the ChoreQuest website.")
        done = item.status == TodoItemStatus.COMPLETED
        was = c["state"] in ("done", "pending")
        if done and not was:
            await self._act("chore_done", id=c["id"], inst=c.get("inst"))
        elif was and not done:
            await self._act("chore_undo", id=c["id"])
