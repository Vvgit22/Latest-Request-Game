import pygame,sys
from level import Level
from default import *


class SceneManager:
    def __init__(self, surface):
        self._scene = Level(surface)

    def run(self, events):
        next_scene = self._scene.run(events)
        if next_scene:
            self._scene = next_scene

    def draw_ui(self, screen):
        if hasattr(self._scene, 'draw_ui'):
            self._scene.draw_ui(screen)


class App:
    def __init__(self):
        pygame.init()
        self._running = True
        self.size = WIDTH, HEIGHT
        self.screen = pygame.display.set_mode(self.size)
        pygame.display.set_caption('ReQuest')
        self._game_surf = pygame.Surface((WIDTH // SCALE, HEIGHT // SCALE))
        self.scene_manager = SceneManager(self._game_surf)

    def run(self):
        while self._running:
            events = pygame.event.get()
            for event in events:
                self.on_event(event)

            self._game_surf.fill('black')
            self.scene_manager.run(events)
            scaled = pygame.transform.scale(self._game_surf, (WIDTH, HEIGHT))
            self.screen.blit(scaled, (0, 0))
            self.scene_manager.draw_ui(self.screen)
            pygame.display.update()

        pygame.quit()
        sys.exit()

    def on_event(self, event):
        if event.type == pygame.QUIT:
            self._running = False


if __name__ == "__main__":
    theApp = App()
    theApp.run()