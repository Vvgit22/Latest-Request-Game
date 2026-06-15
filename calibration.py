import pygame
import sys
from battle import BattleScreen


class CalibrationScreen:
    INSTRUCTIONS = [
        "Hold arm at REST position",
        "Move to MAX position",
        "Confirming with device...",
    ]

    CALIB_DELAY = 300  # 10 seconds at 60 fps

    def __init__(self, player, enemy, ble_controller, back_to, surface):
        self.player = player
        self.enemy = enemy
        self.ble_controller = ble_controller
        self.back_to = back_to
        self.display_surface = surface
        self.step = -1
        self._timer = self.CALIB_DELAY
        self._waiting_start_ok = False
        self.prev_space = False
        self.font = pygame.font.Font('graphics/m5x7.ttf', 32)
        self.background_img = pygame.image.load('graphics/battle-bg.png').convert_alpha()

    def run(self, events=None):
        self.display_surface.fill((20, 20, 40))
        self.display_surface.blit(self.background_img)

        for event in (events or []):
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return self.back_to

        if self.step == -1:
            keys = pygame.key.get_pressed()
            space_down = keys[pygame.K_SPACE]
            if space_down and not self.prev_space:
                self.step = 0
                self._timer = self.CALIB_DELAY
            self.prev_space = space_down
        elif self.step == 2:
            if self.ble_controller.get_and_clear_calib_max_confirmed():
                self.ble_controller.send_command(f"SET_REPS:{self.enemy.hp}")
                self.ble_controller.send_command("START_GAME")
                return BattleScreen(
                    self.player, self.enemy,
                    back_to=self.back_to,
                    surface=self.display_surface,
                    ble_controller=self.ble_controller,
                )
        else:
            if self._waiting_start_ok:
                if self.ble_controller.get_and_clear_calib_start_ok():
                    self._waiting_start_ok = False
                    self.step = 1
                    self._timer = self.CALIB_DELAY
            else:
                self._timer -= 1
                if self._timer <= 0:
                    if self.step == 0:
                        self.ble_controller.send_command("CALIB_START")
                        self._waiting_start_ok = True
                    elif self.step == 1:
                        self.ble_controller.send_command("CALIB_MAX")
                        self.step += 1
                        self._timer = self.CALIB_DELAY
        return None

    def draw_ui(self, screen):
        w = screen.get_width()
        h = screen.get_height()

        if self.step == -1:
            title_surf = self.font.render("EXERCISE", True, (220, 180, 80))
            screen.blit(title_surf, title_surf.get_rect(center=(w // 2, h // 2 - 80)))
            exercise_surf = self.font.render(self.enemy.exercise, True, (220, 220, 220))
            screen.blit(exercise_surf, exercise_surf.get_rect(center=(w // 2, h // 2 - 30)))
            ready_surf = self.font.render("Get ready to exercise!", True, (180, 220, 180))
            screen.blit(ready_surf, ready_surf.get_rect(center=(w // 2, h // 2 + 20)))
            hint_surf = self.font.render("SPACE: Begin calibration   ESC: Skip fight", True, (160, 160, 160))
            screen.blit(hint_surf, hint_surf.get_rect(center=(w // 2, h // 2 + 70)))
        else:
            if 0 <= self.step < 2:
                step_surf = self.font.render(f"CALIBRATION ({self.step + 1}/2)", True, (220, 180, 80))
                screen.blit(step_surf, (w // 2 - step_surf.get_width() // 2, h // 2 - 80))
                if self._waiting_start_ok:
                    hint_surf = self.font.render("Waiting for device...   ESC: Skip fight", True, (160, 160, 160))
                else:
                    seconds_left = max(1, -(-self._timer // 60))
                    hint_surf = self.font.render(f"Auto-confirming in {seconds_left}s   ESC: Skip fight", True, (160, 160, 160))
                screen.blit(hint_surf, (w // 2 - hint_surf.get_width() // 2, h // 2 + 30))

            instr_surf = self.font.render(self.INSTRUCTIONS[self.step], True, (220, 220, 220))
            screen.blit(instr_surf, (w // 2 - instr_surf.get_width() // 2, h // 2 - 30))

            # live stretch bar centred below hint text
            BAR_MAX_W = 200
            BAR_H = 14
            fraction = 0.0 if self.step == 0 else 1.0
            bar_x = w // 2 - BAR_MAX_W // 2
            bar_y = h // 2 + 70
            fill_w = max(1, int(BAR_MAX_W * fraction))
            pygame.draw.rect(screen, (60, 60, 60),   (bar_x, bar_y, BAR_MAX_W, BAR_H))
            pygame.draw.rect(screen, (80, 200, 120), (w // 2 - fill_w // 2, bar_y, fill_w, BAR_H))
