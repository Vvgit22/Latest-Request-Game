import pygame
import sys
from default import ENEMY_DATA
import request_bridge


class BattleScreen:
    def __init__(self, player, enemy, back_to, surface, ble_controller=None):
        self.player = player
        self.enemy = enemy
        self.exercise = enemy.exercise
        self.back_to = back_to
        self.display_surface = surface
        self.ble_controller = ble_controller
        self.enemy_hp = enemy.hp
        self.font = pygame.font.Font('graphics/m5x7.ttf', 32)
        heart = pygame.image.load('graphics/hp2.png').convert_alpha()
        self.heart_img = pygame.transform.scale(heart, (32, 32))
        self._charge = 0
        self._charge_locked = False
        self._flash_timer = 0
        self._death_timer = 0
        self._victory = False
        self._xp_gained = 0
        self._levelled_up = False
        self._rep_grace = True
        self.background_img = pygame.image.load('graphics/battle-bg.png').convert_alpha()
        self.bar_frames = [
            pygame.image.load(f'graphics/bar/bar{i}.png').convert_alpha()
            for i in range(1, 18)
        ]

        if self.ble_controller and self.ble_controller.is_connected():
            self.ble_controller.get_and_clear_reps()
            self.ble_controller.get_and_clear_task_complete()

    def run(self, events=None):
        self.display_surface.fill((20, 20, 40))
        self.display_surface.blit(self.background_img, (0, 0))

        w = self.display_surface.get_width()
        h = self.display_surface.get_height()

        # draw player, bar, and enemy sprites
        player_sprite = self.player.animations['right'][0]
        self.display_surface.blit(player_sprite, (w // 4 - 8, h // 2 - 8))
        if self.ble_controller and self.ble_controller.is_connected():
            fraction = self.ble_controller.get_dist_fraction()
        else:
            fraction = self._charge / 60
        bar_img = self.bar_frames[min(int(fraction * 16), 16)]
        bar_x = w // 4 - 8 + player_sprite.get_width() // 2 - bar_img.get_width() // 2
        bar_y = h // 2 - 8 + player_sprite.get_height() + 30
        self.display_surface.blit(bar_img, (bar_x, bar_y))
        if self.enemy.alive():
            self.enemy.animate()
            img = self.enemy.image
            if self._flash_timer > 0:
                self._flash_timer -= 1
                if self._flash_timer % 8 >= 4:
                    img = img.copy()
                    img.fill((255, 255, 255), special_flags=pygame.BLEND_RGB_MAX)
            flipped = pygame.transform.flip(img, True, False)
            self.display_surface.blit(flipped, (3 * w // 4 - 8, h // 2 - 8))

        # handle input (skipped during death sequence)
        if self._death_timer == 0:
            if self.ble_controller and self.ble_controller.is_connected():
                if self._rep_grace:
                    self._rep_grace = False
                    self.ble_controller.get_and_clear_reps()
                else:
                    reps = self.ble_controller.get_and_clear_reps()
                    if reps > 0:
                        self.enemy_hp -= reps
                        self._flash_timer = 60
                if self.ble_controller.get_and_clear_task_complete():
                    self.enemy_hp = 0
                    self._flash_timer = 60
            else:
                CHARGE_MAX = 60
                keys = pygame.key.get_pressed()
                if keys[pygame.K_SPACE]:
                    if not self._charge_locked:
                        self._charge = min(self._charge + 1, CHARGE_MAX)
                        if self._charge >= CHARGE_MAX:
                            self.enemy_hp -= 1
                            self._charge = 0
                            self._flash_timer = 60
                            self._charge_locked = True
                else:
                    self._charge = 0
                    self._charge_locked = False

        for event in (events or []):
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if self.ble_controller and self.ble_controller.is_connected():
                    self.ble_controller.send_command("RESET_ALL")
                return self.back_to

        if self.enemy_hp <= 0 and self._death_timer == 0 and not self._victory:
            self._death_timer = 180  # 3 seconds at 60 fps

        if self._death_timer > 0:
            self._death_timer -= 1
            if self._death_timer == 0:
                self.enemy.kill()
                if self.ble_controller and self.ble_controller.is_connected():
                    self.ble_controller.send_command("RESET_ALL")
                xp = ENEMY_DATA[self.enemy.enemy_type]['xp']
                self._levelled_up = self.player.add_xp(xp)
                self._xp_gained = xp
                self._victory = True
                last_enemy = not self.back_to.enemy_sprites
                request_bridge.save_result(
                    exercise=self.exercise,
                    reps=getattr(self.enemy, 'reps', self.enemy.hp),
                    sets=getattr(self.enemy, 'sets', 1),
                    xp=xp,
                )
                if last_enemy:
                    self.back_to.drop_key(self.enemy.rect.center)

        if self._victory:
            for event in (events or []):
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    return self.back_to

        return None

    def draw_ui(self, screen):
        scale = screen.get_width() // self.display_surface.get_width()
        w_small = self.display_surface.get_width()
        h_small = self.display_surface.get_height()

        ex_small = 3 * w_small // 4 - 8
        ey_small = h_small // 2 - 8
        sprite_w = self.enemy.image.get_width()
        sprite_h = self.enemy.image.get_height()

        enemy_bottom = (ey_small + sprite_h) * scale + 120

        # Show ONE set's worth of hearts at a time (reps per set), refilling each
        # new set, so a 15-rep set never overflows the screen.
        reps_per_set = max(1, getattr(self.enemy, 'reps', self.enemy_hp))
        total_sets   = max(1, getattr(self.enemy, 'sets', 1))
        total_hp     = reps_per_set * total_sets
        remaining    = max(0, self.enemy_hp)
        if remaining == 0:
            hearts = 0
        elif remaining % reps_per_set == 0:
            hearts = reps_per_set            # a fresh, full set
        else:
            hearts = remaining % reps_per_set
        current_set = min(total_sets, (total_hp - remaining) // reps_per_set + 1)

        # Lay the row out so it always fits on screen, shifted left of the enemy.
        spacing  = 36
        row_w    = hearts * spacing
        enemy_cx = ex_small * scale + (sprite_w * scale) // 2
        start_x  = enemy_cx - row_w // 2
        start_x  = min(start_x, screen.get_width() - row_w - 24)
        start_x  = max(24, start_x)
        for i in range(hearts):
            screen.blit(self.heart_img, (start_x + i * spacing, enemy_bottom))

        name_surf = self.font.render(
            f'{self.enemy.enemy_type.capitalize()}   Set {current_set}/{total_sets}',
            False, (220, 220, 220))
        name_y = enemy_bottom + self.heart_img.get_height() + 6
        screen.blit(name_surf, (start_x, name_y))

        w_screen, h_screen = screen.get_size()
        if self._victory:
            cx = w_screen // 2
            cy = h_screen // 2 - 48
            line1 = self.font.render(f'Enemy defeated!  +{self._xp_gained} XP', False, (255, 220, 80))
            if self._levelled_up:
                line2 = self.font.render(f'LEVEL UP!  Now Lv.{self.player.level}', False, (100, 255, 100))
            else:
                line2 = self.font.render(f'Lv.{self.player.level}   {self.player.xp} / {self.player.xp_to_next()} XP', False, (180, 180, 180))
            line3 = self.font.render('Press SPACE to continue', False, (160, 160, 160))
            screen.blit(line1, line1.get_rect(center=(cx, cy)))
            screen.blit(line2, line2.get_rect(center=(cx, cy + 40)))
            screen.blit(line3, line3.get_rect(center=(cx, cy + 80)))
        else:
            if self.ble_controller and self.ble_controller.is_connected():
                hint = 'REP: Attack   ESC: Flee'
            else:
                hint = 'HOLD SPACE: Attack   ESC: Flee'
            hint_text = self.font.render(hint, False, (180, 180, 180))
            screen.blit(hint_text, (16, h_screen - 48))

            player_sprite = self.player.animations['right'][0]
            bar_sample = self.bar_frames[0]
            bar_y_small = h_small // 2 - 8 + player_sprite.get_height() + 35
            bar_bottom_screen = (bar_y_small + bar_sample.get_height()) * scale
            bar_cx_screen = (w_small // 4 - 8 + player_sprite.get_width() // 2) * scale
            bar_w_screen = bar_sample.get_width() * scale

            raw = f'Complete 1 rep of {self.exercise} to deal damage'
            words = raw.split()
            lines, current = [], ''
            for word in words:
                test = (current + ' ' + word).strip()
                if self.font.size(test)[0] <= bar_w_screen:
                    current = test
                else:
                    if current:
                        lines.append(current)
                    current = word
            if current:
                lines.append(current)

            text_y = bar_bottom_screen + 12
            for line in lines:
                surf = self.font.render(line, False, (200, 200, 200))
                screen.blit(surf, surf.get_rect(center=(bar_cx_screen, text_y)))
                text_y += surf.get_height() + 2
