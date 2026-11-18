# ChoreQuest for Home Assistant

Bring your family's [ChoreQuest](https://chores.maraishome.com) chore chart into Home Assistant. Each family member's **checklist** and **chores** for today appear as Home Assistant to-do lists, plus a few sensors you can use on dashboards and in automations.

It's handy when kids can't open a browser (for example during phone downtime) but can still use the Home Assistant app.

## What you get
For each person in your family:
- **`todo.<name>_checklist`:** today's checklist, synced both ways. You can add, rename, tick, untick and delete tasks. Only tasks in their current time window show, just like on the site. A task added in Home Assistant shows all day, every day; set its times on the ChoreQuest site.
- **`todo.<name>_chores`:** today's chores. Tick to mark done and untick to undo. Chores that need a parent's OK still wait for one. Up-for-grabs chores show for everyone they're offered to, and ticking one grabs it and marks it done in one go. Chores are created and edited on the ChoreQuest site.
- **Sensors:** Tasks left, Chores left, Coins, Streak and Level. The "left" sensors list the names in their attributes.

Home Assistant checks for changes every minute. Changes you make in Home Assistant reach ChoreQuest straight away and show in its activity feed as "via Home Assistant".

## Requirements
- A ChoreQuest family, where you are a parent or adult in the family.
- Home Assistant 2026.2 or newer.

## Install
1. **Add the integration.** In Home Assistant go to **Settings → Marketplace → Add from link**, enter `jakesCT/chorequest-homeassistant`, and install **ChoreQuest**. On Home Assistant older than 2026.11, use **HACS → ⋮ → Custom repositories** with type **Integration** instead. Restart Home Assistant if asked.
2. **Make a key.** On the ChoreQuest site go to **Family → Home Assistant → ＋ New key** and copy the key. It's shown only once, so keep it private: it can read and change your family's lists.
3. **Connect.** In Home Assistant go to **Settings → Devices & services → Add integration → ChoreQuest**. Enter your ChoreQuest site address (for example `https://chores.maraishome.com`) and paste the key.

Each family member appears as a device. Their lists show under **To-do lists** in the Home Assistant sidebar and app.

**Removing access:** delete the key on the site under Family → Home Assistant and Home Assistant stops syncing straight away. If that happens by mistake, Home Assistant shows a **Reconfigure** prompt; make a new key and paste it there.

**Updates** arrive through the Marketplace. You'll see "ChoreQuest update available" in Settings.

**Running your own ChoreQuest server?** Use its address instead, for example `http://192.168.1.20:3040` on your local network.

## Example dashboard card
```yaml
type: vertical-stack
cards:
  - type: heading
    heading: Michael's ChoreQuest
  - type: horizontal-stack
    cards:
      - { type: tile, entity: sensor.michael_tasks_left, name: Tasks left }
      - { type: tile, entity: sensor.michael_chores_left, name: Chores left }
  - { type: todo-list, entity: todo.michael_checklist, title: Checklist }
  - { type: todo-list, entity: todo.michael_chores, title: Chores, hide_create: true }
```

## Example automation: morning reminder on a speaker
```yaml
alias: Morning checklist reminder
triggers:
  - trigger: time
    at: "06:45:00"
conditions:
  - condition: numeric_state
    entity_id: sensor.michael_tasks_left
    above: 0
actions:
  - action: tts.speak
    target:
      entity_id: tts.google_translate_en_com
    data:
      media_player_entity_id: media_player.kitchen
      message: >
        Michael, you still have {{ states('sensor.michael_tasks_left') }} things to do:
        {{ state_attr('sensor.michael_tasks_left', 'tasks') | join(', ') }}.
```
