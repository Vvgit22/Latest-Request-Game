import pygame
import sys


class ConnectionScreen:
    def __init__(self, ble_controller, next_scene):
        self.ble_controller = ble_controller
        self.next_scene = next_scene
        self.font = pygame.font.Font('graphics/m5x7.ttf', 32)
        self._tick = 0

    def run(self, events=None):
        self._tick += 1

        for event in (events or []):
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                return self.next_scene

        if self.ble_controller.is_connected():
            return self.next_scene

        return None

    def draw_ui(self, screen):
        w = screen.get_width()
        h = screen.get_height()

        dots = '.' * ((self._tick // 30) % 4)
        status_surf = self.font.render(f"Searching for StellaController{dots}", True, (220, 220, 220))
        hint_surf = self.font.render("SPACE: Play without controller", True, (140, 140, 140))

        screen.blit(status_surf, (w // 2 - status_surf.get_width() // 2, h // 2 - 30))
        screen.blit(hint_surf,   (w // 2 - hint_surf.get_width()   // 2, h // 2 + 20))
