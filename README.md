# ChoreQuest for Home Assistant

Shows each family member's **checklist** and **chores** from a [ChoreQuest](https://chores.maraishome.com) family chore chart as Home Assistant to-do lists, plus a few sensors.

- **Checklist:** syncs both ways. You can add, rename, tick, untick and delete tasks. Only tasks inside their current time window show, just like on the site. A task added in Home Assistant is "any time, every day"; set its times on the site.
- **Chores:** tick to mark done and untick to undo. Chores that need a parent's OK still wait for one. Up-for-grabs chores show for everyone they're offered to, and ticking one grabs it and marks it done in one go. Chores are created and edited on the website.
- **Sensors per person:** Tasks left, Chores left, Coins, Streak and Level. The "left" sensors list the names in their attributes.
- Home Assistant checks for changes every minute. Changes made in Home Assistant reach the site straight away and show in its activity feed as "via Home Assistant".

## Install
1. In Home Assistant go to **Settings → Marketplace → Add from link** and enter `jakesCT/chorequest-homeassistant`. (With older HACS: **HACS → ⋮ → Custom repositories**, type **Integration**.)
2. Install **ChoreQuest** and restart Home Assistant if asked.
3. On the ChoreQuest site, go to **Family → Home Assistant → New key** and copy the key. It is shown only once.
4. In Home Assistant, go to **Settings → Devices & services → Add integration → ChoreQuest**, then enter the site address (on your own network the server's local address, such as `http://10.10.1.20:3040`, is fastest) and paste the key.

Each person appears as a device with `todo.<name>_checklist`, `todo.<name>_chores` and the sensors. If a key is removed on the site, Home Assistant asks you to reconfigure; make a new key and paste it there.

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
