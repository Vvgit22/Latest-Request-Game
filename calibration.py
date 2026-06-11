import pygame
import sys
from battle import BattleScreen


class CalibrationScreen:
    INSTRUCTIONS = [
        "Hold arm at REST position",
        "Move to MAX position",
        "Confirming with device...",
    ]

    def __init__(self, player, enemy, ble_controller, back_to, surface):
        self.player = player
        self.enemy = enemy
        self.ble_controller = ble_controller
        self.back_to = back_to
        self.display_surface = surface
        self.step = 0
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

        if self.step == 2:
            if self.ble_controller.get_and_clear_calib_max_confirmed():
                self.ble_controller.send_command("START_GAME")
                return BattleScreen(
                    self.player, self.enemy,
                    back_to=self.back_to,
                    surface=self.display_surface,
                    ble_controller=self.ble_controller,
                )
        else:
            keys = pygame.key.get_pressed()
            space_down = keys[pygame.K_SPACE]
            if space_down and not self.prev_space:
                if self.step == 0:
                    self.ble_controller.send_command("CALIB_START")
                    self.step = 1
                elif self.step == 1:
                    self.ble_controller.send_command("CALIB_MAX")
                    self.step = 2
            self.prev_space = space_down
        return None

    def draw_ui(self, screen):
        w = screen.get_width()
        h = screen.get_height()

        if self.step < 2:
            step_surf = self.font.render(f"CALIBRATION ({self.step + 1}/2)", True, (220, 180, 80))
            screen.blit(step_surf, (w // 2 - step_surf.get_width() // 2, h // 2 - 80))
            hint_surf = self.font.render("SPACE: Confirm   ESC: Skip fight", True, (160, 160, 160))
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
