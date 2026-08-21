ReQuest Companion

Run the local PyGame application directly from the ReQuest web prototype.

The PyGame game remains in its own repository and keeps its existing sensor integration and game logic. The ReQuest companion acts only as a local bridge between the browser dashboard and the game.

⸻

Overview

The companion provides three main functions:

1. Launch the PyGame game from the browser
2. Send exercise prescriptions from the dashboard to the game
3. Send completed exercise/workout results back to the dashboard

The communication flow is:

ReQuest Dashboard
       │
       │ reps / sets / exercise plan
       ▼
   session.json
       │
       ▼
    PyGame
       │
       │ exercise completed
       ▼
request_bridge.save_result(...)
       │
       ▼
ReQuest Dashboard

⸻

1. Setup

Install the companion dependencies:

pip install -r requirements.txt

Start the companion and provide the path to the PyGame entry script:

python bridge.py --game /path/to/game_repo/game.py

For testing without the full game:

python bridge.py --game demo_game.py

Then open:

http://localhost:8765

The companion serves request-app.html.

Log in and open the Play page.

⸻

2. Launching the Game

The Crystal Caverns screen contains three controls:

Button	Behaviour
▶ LAUNCH GAME	Starts the PyGame script in its normal native window
LAUNCH + MIRROR	Starts the native PyGame window and streams a live copy into the web page
STOP GAME	Terminates the running game

A browser cannot execute local Python commands directly.

The companion solves this by exposing:

POST /api/launch

The browser calls this endpoint and the companion launches the configured PyGame script locally.

The native PyGame window remains the primary game interface.

⸻

3. Dashboard → Game

The dashboard sends the prescribed workout to the game.

The plan contains one entry per exercise:

{
  "patient": "Marcus",
  "plan": [
    {
      "exercise": "Shoulder External Rotation",
      "reps": 12,
      "sets": 3
    },
    {
      "exercise": "Banded I-Y-T Raises",
      "reps": 15,
      "sets": 3
    },
    {
      "exercise": "Single-Arm Row to Press",
      "reps": 10,
      "sets": 3
    }
  ],
  "current": 0,
  "resistance": "medium",
  "updated": 1700000000.0
}

This configuration is written to:

session.json

next to the game script.

The dashboard updates the file whenever reps or sets change.

⸻

Where Reps and Sets Can Be Changed

Patient Play View

The Game link card allows:

* Reps per set
* Number of sets

Press:

Send to game

to send the updated values.

Physio Portal

Changes made under:

Adjust program → Done

are also sent to the game.

⸻

4. Reading the Workout Plan in PyGame

Import the helper:

import request_bridge

Get the full prescribed workout:

plan = request_bridge.get_plan()

Example:

[
    {
        "exercise": "Shoulder External Rotation",
        "reps": 12,
        "sets": 3
    },
    {
        "exercise": "Banded I-Y-T Raises",
        "reps": 15,
        "sets": 3
    }
]

Create one enemy encounter for each exercise.

For example:

for exercise in plan:
    create_enemy(
        exercise_name=exercise["exercise"],
        reps=exercise["reps"],
        sets=exercise["sets"]
    )

In the ReQuest game concept:

1 prescribed rep = 1 enemy hit point

The dashboard does not modify lives, enemy behaviour, score, or other internal game variables.

Those remain controlled by the game.

⸻

5. Reading Session Data

There are several supported methods.

Recommended: request_bridge

import request_bridge
cfg = request_bridge.get_session()

Get the current exercise:

exercise = request_bridge.current_exercise()

Get the full plan:

plan = request_bridge.get_plan()

⸻

Direct File Access

Read:

session.json

The path is also available in:

REQUEST_BRIDGE_SESSION

⸻

HTTP API

GET /api/session

⸻

Live PyGame Event

When the dashboard changes the workout during a running session, the companion can emit:

request_bridge.SESSION_EVENT

which corresponds to:

USEREVENT + 7

Example:

if event.type == request_bridge.SESSION_EVENT:
    cfg = event.session

⸻

6. Game → Dashboard

The main integration point is extremely small.

When an enemy is defeated, report the completed exercise:

request_bridge.save_result(
    exercise=enemy.exercise_name,
    reps=enemy.reps,
    sets=enemy.sets,
    xp=50
)

Call this once when the enemy is defeated.

That is enough for the dashboard to record the exercise.

No continuous rep or ROM streaming is required.

⸻

7. Minimal Game Integration

The minimal required integration is:

import request_bridge
plan = request_bridge.get_plan()
# Build one enemy encounter per exercise in plan.
# When an enemy is defeated:
request_bridge.save_result(
    exercise=enemy.exercise_name,
    reps=enemy.reps,
    sets=enemy.sets,
    xp=50
)

That is the core game ↔ dashboard contract.

⸻

8. Automatic Workout Completion

The dashboard already knows every exercise in the prescribed plan.

It tracks which exercises have been reported as completed.

Once every exercise has been completed, the workout is automatically marked complete.

The dashboard then:

* adds +1 level
* awards 50 XP per completed exercise
* records the workout
* displays a Workout complete notification
* redirects the patient to the post-workout check-in

For example, a three-exercise workout gives:

3 exercises × 50 XP = 150 XP

No additional completion call is normally required.

⸻

Fallback Completion Signal

If enemy names do not exactly match the exercise names in the plan, the final enemy can explicitly mark the workout complete:

request_bridge.save_result(
    exercise=enemy.exercise_name,
    reps=enemy.reps,
    sets=enemy.sets,
    xp=50,
    workout_complete=True
)

This should only be used as a fallback.

⸻

9. Workout Storage

Completed exercise data is stored in:

workout_log.json

next to the game.

Each defeated enemy produces a record similar to:

{
  "exercise": "Shoulder External Rotation",
  "reps": 12,
  "sets": 3,
  "xp": 50
}

A completed workout also creates a summary record containing information such as:

{
  "exercises": 3,
  "xp_total": 150,
  "level_gain": 1
}

⸻

10. Post-Workout Check-In

Once the workout is complete, the patient is automatically taken to the daily check-in.

The check-in includes:

* pain
* soreness
* post-workout self-report

A summary banner shows the workout that was just completed.

⸻

11. Optional Saved Progress

Persistent browser progress is disabled by default.

It can be enabled under:

Settings → Record my progress

When enabled, the browser stores:

* patient level
* check-in history
* messages
* last workout

using:

localStorage

Refreshing the web page therefore does not reset the session.

Selecting New session clears the saved browser progress for a fresh demo.

Completed workouts remain persisted separately in:

workout_log.json

⸻

12. Optional Live Progress Reporting

The main integration only requires save_result() when an enemy is defeated.

Live progress can optionally be reported during gameplay:

request_bridge.report(
    reps_done=hits,
    sets_done=cleared,
    level=lvl,
    score=score
)

The Play page can then display live This session statistics.

At the end of the workout:

request_bridge.save_result(
    reps_done=hits,
    sets_done=cleared,
    level=lvl,
    score=score,
    completed=True
)

If only report() is used and the game closes unexpectedly, the most recently reported values can be saved automatically on exit.

These calls run asynchronously so they do not block the PyGame loop.

⸻

13. Progress API

Available endpoints:

POST /api/progress
POST /api/result
GET /api/results
GET /api/session

⸻

14. Mirror Mode

LAUNCH + MIRROR keeps the native PyGame window running normally while also displaying the game inside the Crystal Caverns page.

The native window remains the recommended way to play.

The mirrored view is intended primarily for:

* demonstrations
* physiotherapist monitoring
* audience viewing
* dashboard integration

Sensor input continues to control the native game directly.

⸻

Mirror Performance

The game thread performs only a small raw-pixel capture.

JPEG encoding and transmission run on a separate worker thread.

If the mirror cannot keep up, frames are dropped instead of slowing the game.

Performance settings are available near the top of:

runner.py

Important parameters:

MIRROR_FPS
JPEG_QUALITY
MAX_WIDTH

For slower machines, reduce these values.

⸻

15. Avoid Reading session.json Every Frame

Do not repeatedly read the file inside the main game loop.

Avoid:

while running:
    cfg = read_session_from_disk()

Instead, load the configuration once:

import request_bridge
cfg = request_bridge.get_session()

Then update it only when the dashboard sends a change:

if event.type == request_bridge.SESSION_EVENT:
    cfg = event.session

request_bridge.get_session() is cached and avoids unnecessary disk access.

⸻

16. Known PyGame Fix

If battle.py contains:

self.display_surface.blit(self.background_img)

PyGame raises:

TypeError: function missing required argument 'dest'

Surface.blit() requires a destination.

Change it to:

self.display_surface.blit(
    self.background_img,
    (0, 0)
)

⸻

17. File Structure

File	Purpose
bridge.py	Local companion server. Serves the web app, launches/stops PyGame, exposes APIs and relays mirror frames
runner.py	Runs the game in mirror mode and streams frames
request-app.html	ReQuest web prototype
request_bridge.py	Helper library used by the PyGame application
demo_game.py	Minimal PyGame implementation for testing the companion
session.json	Current prescribed workout
workout_log.json	Persistent completed workout records

⸻

18. Recommended Play Flow

1. Start bridge.py
        ↓
2. Open http://localhost:8765
        ↓
3. Select / adjust workout
        ↓
4. Dashboard writes session.json
        ↓
5. Launch PyGame
        ↓
6. Game loads exercise plan
        ↓
7. Patient completes enemy encounters
        ↓
8. Game calls save_result() after each enemy
        ↓
9. Dashboard detects full workout completion
        ↓
10. XP + level awarded
        ↓
11. Patient redirected to check-in

⸻

19. Quick Start

Start the companion:

python bridge.py --game /path/to/game.py

Open:

http://localhost:8765

In the game:

import request_bridge
plan = request_bridge.get_plan()

When an enemy is defeated:

request_bridge.save_result(
    exercise=enemy.exercise_name,
    reps=enemy.reps,
    sets=enemy.sets,
    xp=50
)

Everything else — workout completion, XP, level-up, logging and post-workout check-in — is handled by the ReQuest companion and dashboard.

⸻

Compatibility

Tested with:

Python 3.12
pygame-ce 2.5.7

Standard pygame is also supported.

Default companion port:

8765
