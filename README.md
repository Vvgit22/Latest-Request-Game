# ReQuest — physiotherapy dungeon game

The game half of ReQuest, a gamified physiotherapy system built for a
physiotherapy hackathon project. This is the current version; earlier code
lives in [ReQuest-Game](https://github.com/Vvgit22/ReQuest-Game).

A pygame dungeon crawler driven by two Bluetooth (BLE) wristbands instead of
a keyboard: after a calibration step, each prescribed exercise is an enemy
encounter and every completed rep counts as damage. The patient-facing app,
clinician dashboard and backend live in
[ReQuest-Physiotherapy](https://github.com/Vvgit22/ReQuest-Physiotherapy).
More about the project: https://vvgit22.github.io/projects/request/

## Run it

```
pip install pygame bleak
python main.py
```

`ble_controller.py` talks to the wristbands over BLE (`bleak`); the game
still runs without hardware — a keyboard fallback is used when no bands are
found. `request_bridge.py` relays session data to the clinician dashboard.
