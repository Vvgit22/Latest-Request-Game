"""
demo_game.py — a faithful, runnable reference for the agreed contract.
This stands in for the real game so you can see exactly which helper calls to
make. Plug the same calls into your own battle/game loop.

Flow:
  1. read the workout plan from the dashboard  -> request_bridge.get_plan()
  2. build ONE enemy encounter per exercise (reps/sets = how much work to win)
  3. when an enemy is defeated -> request_bridge.save_result(exercise, reps, sets, xp=50)
  4. when every enemy is defeated the dashboard auto-marks the workout done
     (+1 character level) and sends the patient to their check-in.
No live rep/ROM reporting — only the discrete "enemy defeated" save.
"""
import time, pygame
import request_bridge

XP_PER_EXERCISE = 50

pygame.init()
screen = pygame.display.set_mode((800, 500))
pygame.display.set_caption("ReQuest - pygame demo")
clock = pygame.time.Clock()
big = pygame.font.SysFont("monospace", 28, bold=True)
fnt = pygame.font.SysFont("monospace", 18)

def load_plan():
    p = request_bridge.get_plan()
    return p if p else [{"exercise": "Band pull-apart", "reps": 10, "sets": 3}]

plan = load_plan()
enc = 0                                  # current enemy / exercise index
hits = 0                                 # hits landed on the current enemy
needed = plan[0]["reps"] * plan[0]["sets"]   # total reps to defeat enemy 0
level = 1
flash = 0; px = 400; msg_until = 0

def reset_workout():
    global plan, enc, hits, needed
    plan = load_plan(); enc = 0; hits = 0
    needed = plan[0]["reps"] * plan[0]["sets"]

running = True
while running:
    cur = plan[min(enc, len(plan) - 1)]
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False
        elif e.type == request_bridge.SESSION_EVENT:    # dashboard changed the plan
            reset_workout(); flash = 12
        elif e.type == pygame.KEYDOWN:
            if e.key == pygame.K_SPACE and enc < len(plan):
                hits += 1; flash = 6
                if hits >= needed:                       # ENEMY DEFEATED
                    # --- the one call you need on each enemy defeat ---
                    request_bridge.save_result(exercise=cur["exercise"],
                                               reps=cur["reps"], sets=cur["sets"],
                                               xp=XP_PER_EXERCISE)
                    enc += 1; hits = 0
                    if enc >= len(plan):                 # all enemies down = workout done
                        level += 1                       # dashboard also adds +1 level
                        msg_until = time.time() + 2.5; flash = 12
                        reset_workout()
                    else:
                        needed = plan[enc]["reps"] * plan[enc]["sets"]
            if e.key == pygame.K_LEFT:  px = max(60, px - 30)
            if e.key == pygame.K_RIGHT: px = min(740, px + 30)

    screen.fill((24, 20, 50) if not flash else (40, 30, 90))
    flash = max(0, flash - 1)
    pygame.draw.rect(screen, (220, 80, 110), (px - 60, 180, 120, 120), border_radius=14)
    hp = max(0, needed - hits)
    if needed:
        w = int(116 * hp / needed)
        pygame.draw.rect(screen, (255, 216, 107), (px - 58, 150, max(0, w), 12), border_radius=6)
    for f, txt, y in [
        (big, cur["exercise"], 32),
        (fnt, f"Enemy {min(enc+1,len(plan))}/{len(plan)}   HP {hp}/{needed}   ({cur['reps']} reps x {cur['sets']} sets)", 82),
        (fnt, f"Level {level}   +{XP_PER_EXERCISE} XP per enemy defeated", 110),
        (fnt, f"FPS {int(clock.get_fps())}   SPACE = one rep   ARROWS move", 460),
    ]:
        screen.blit(f.render(txt, True, (235, 235, 250)), (40, y))
    if time.time() < msg_until:
        screen.blit(big.render("WORKOUT COMPLETE  -  +1 LEVEL!", True, (22, 196, 172)), (120, 320))
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
