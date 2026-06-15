# ReQuest dashboard ↔ game — verified integration for `Latest-Request-Game`

Checked against the actual repo HEAD (`github.com/Vvgit22/Latest-Request-Game`),
patched, byte-compiled, and tested end-to-end headlessly. Two things first:

> ### 🔴 The game does not start right now
> `battle.py` line 4 is `import request_bridge`, but there is **no
> `request_bridge.py` at the repo root** — it only lives inside
> `request-bridge 5/`. When Python runs `main.py`, the import path is the repo
> root, so this import fails and the whole game crashes on launch. **Fix:** put a
> copy of `request_bridge.py` at the repo root (step 1 below). This is the single
> most important change.

> ### ⛔ Do NOT copy the older `.py` files over this repo
> The patched files shipped with the old `CHANGES.md` were from an earlier build.
> This repo is newer (tutorial level + NPC, items/keys + door, player XP &
> leveling via `save.json`, charge-bar battle, randomised spawns). Overwriting
> would delete that work. Apply only the small edits below.

---

## What changes (6 items; `level.py` is *not* touched)

| File | Change | Why |
|---|---|---|
| `request_bridge.py` | **add at repo root** (copy of `request-bridge 5/request_bridge.py`) | without it the `import request_bridge` in `battle.py` crashes the game |
| `default.py` | append `apply_prescription()` | maps the dashboard plan -> enemy HP (= reps x sets), by exercise name |
| `main.py` | call `apply_prescription()` after `pygame.init()` | runs before enemies are built |
| `enemy.py` | store `self.reps` / `self.sets` | so the defeat-save reports the real prescribed numbers |
| `battle.py` | blit fix + `save_result(...)` on defeat | logs each exercise; completes the workout on the last enemy |
| `calibration.py` | blit fix | same `blit()` missing-dest bug |

The `import request_bridge` line in `battle.py` is **already present** — no import
edit needed.

---

## Fastest path: apply the patch + drop in the helper

From the repo root:

```bash
# 1) the helper must be importable (this is what makes the game start)
cp "request-bridge 5/request_bridge.py" request_bridge.py

# 2) apply the code edits
git apply request_game_integration.patch
```

Then commit. If you'd rather not use the patch, the five edited files are
included ready-to-commit, or apply the edits by hand below.

---

## The edits by hand (anchored to current line numbers)

**1. `request_bridge.py` at repo root** — `cp "request-bridge 5/request_bridge.py" request_bridge.py`. (This v5 has no `finish_workout()`; that's fine — see battle.py below.)

**2. `default.py`** — append at the end:

```python
def apply_prescription():
    """Pull the prescribed exercises (name, reps, sets) from the ReQuest
    dashboard into ENEMY_DATA before the enemies are created.
    Enemy HP = reps * sets. Matched to enemies by exercise name.
    Safe if the dashboard isn't running: leaves ENEMY_DATA untouched."""
    try:
        import request_bridge
        plan = request_bridge.get_plan()
    except Exception:
        return
    by_name = {e.get('exercise'): e for e in plan}
    for data in ENEMY_DATA.values():
        p = by_name.get(data.get('exercise'))
        if p:
            data['reps'] = int(p['reps'])
            data['sets'] = int(p['sets'])
            data['hp'] = max(1, int(p['reps']) * int(p['sets']))
```

**3. `main.py`** (App.__init__, ~line 34) — add one line after `pygame.init()`:

```python
    def __init__(self):
        pygame.init()
        apply_prescription()          # pull prescribed reps/sets into the enemies
        self._running = True
```

**4. `enemy.py`** (~line 13) — add two lines after `self.hp = data['hp']`:

```python
        self.hp = data['hp']
        self.reps = data.get('reps', data['hp'])
        self.sets = data.get('sets', 1)
        self.exercise = data['exercise']
```

**5a. `battle.py`** line 39 — blit fix:

```python
        self.display_surface.blit(self.background_img, (0, 0))
```

**5b. `battle.py`** (death-timer-complete block, ~line 116) — replace:

```python
                self._xp_gained = xp
                self._victory = True
                if not self.back_to.enemy_sprites:
                    self.back_to.drop_key(self.enemy.rect.center)
```

with:

```python
                self._xp_gained = xp
                self._victory = True
                last_enemy = not self.back_to.enemy_sprites
                request_bridge.save_result(
                    exercise=self.exercise,
                    reps=getattr(self.enemy, 'reps', self.enemy.hp),
                    sets=getattr(self.enemy, 'sets', 1),
                    xp=xp,
                    workout_complete=last_enemy,
                )
                if last_enemy:
                    self.back_to.drop_key(self.enemy.rect.center)
```

`workout_complete=last_enemy` fires the moment the **final in-game enemy** dies,
so the dashboard completes the workout (+1 level -> check-in) — this is what makes
the separate `level.py` `finish_workout()` patch unnecessary, and it works even
when the plan lists more exercises than there are enemies (your current
`session.json` has 3 exercises; the game has 2 enemies).

*XP:* this reports each enemy's own XP (ghost 50 / skeleton 100). For a flat +50,
change `xp=xp` -> `xp=50`.

**6. `calibration.py`** line 30 — blit fix:

```python
        self.display_surface.blit(self.background_img, (0, 0))
```

---

## Left untouched on purpose

`level.py`, `player.py`, `tutorial_level.py`, `npc.py`, `finish.py`, `item.py`,
`entity.py`, `tile.py`, `connection_screen.py`, `ble_controller.py`. The only two
`blit()` missing-dest bugs in the whole repo are the two fixed above; the tutorial
and NPC code are clean.

---

## Demo configuration (settings, not bugs)

- **Names must match for HP sync.** Enemy HP updates only when the plan uses the
  exact enemy strings: `Shoulder External Rotation` (ghost), `Banded I-Y-T
  Raises` (skeleton). Other names are ignored in-game (the enemy keeps default
  HP); the game still runs and still completes.
- **HP = reps x sets.** Your current plan gives ghost 9x3 = 27 and skeleton
  15x3 = 45 hits. For a snappy live demo, prescribe small numbers. Tune in the
  dashboard, not the code.
- **BLE path is unaffected** — `SET_REPS` is still sent from `calibration.py`
  using `self.enemy.hp` (= reps x sets after the prescription).
- **Standalone still works** — with no companion running, `get_plan()` returns a
  default and `save_result()` no-ops, so `python main.py` behaves as before
  (once `request_bridge.py` is at the root so the import resolves).

---

## What I verified (pygame-ce 2.5.7, headless)

- All modules byte-compile with the patches applied. [OK]
- `apply_prescription()` against the real `session.json`: ghost -> 27 HP,
  skeleton -> 45 HP, reps/sets stored, XP preserved, unmatched 3rd exercise
  ignored. [OK]
- Full save path through the real `bridge.py`: defeating both enemies logged
  both exercises to `workout_log.json`; the last enemy's
  `workout_complete=True` produced a workout summary (`level_gain` 1, `xp_total`
  150) despite the 3-exercise / 2-enemy mismatch. [OK]

---

## Run it

In the companion folder (`request-bridge 5/`):

```bash
pip install -r requirements.txt
python bridge.py --game /path/to/Latest-Request-Game/main.py
```

Open http://localhost:8765 -> log in -> **Play** -> **LAUNCH GAME** (or
**LAUNCH + MIRROR**). Set reps/sets in the Play "Game link" card (or physio
*Adjust program*) -> **Send to game** -> relaunch to rebuild the enemies. Defeat
them; on the last enemy the dashboard shows the workout complete and (patient
view) jumps to the check-in.
