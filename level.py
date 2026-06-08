import pygame
from default import *
from tile import Tile
from player import Player
from enemy import Enemy
from battle import BattleScreen
from finish import FinishScreen


class Level:
    def __init__(self, surface):
        self.display_surface = surface

        self.visible_sprites = YSortCameraGroup(surface)
        self.obstacle_sprites = pygame.sprite.Group()
        self.enemy_sprites = pygame.sprite.Group()

        self.create_map()

    def create_map(self):
        for row_index, row in enumerate(WORLD_MAP):
            for col_index, col in enumerate(row):
                x = col_index * TILESIZE
                y = row_index * TILESIZE
                if col == 'x':
                    Tile((x, y), [self.visible_sprites, self.obstacle_sprites],col)
                elif col == 'p':
                    self.player = Player((x, y), [self.visible_sprites], self.obstacle_sprites)
                    Tile((x,y), [self.visible_sprites], ' ')
                elif col in ENEMY_MAP:
                    Enemy((x, y), [self.visible_sprites, self.enemy_sprites], self.obstacle_sprites, ENEMY_MAP[col])
                    Tile((x,y), [self.visible_sprites], ' ')
                elif col == ' ':
                    Tile((x,y), [self.visible_sprites], col)

    def _check_battle(self):
        hits = pygame.sprite.spritecollide(self.player, self.enemy_sprites, False)
        if hits:
            return BattleScreen(self.player, hits[0], back_to=self, surface=self.display_surface)
        return None

    def run(self, events=None):
        self.visible_sprites.update()
        self.visible_sprites.custom_draw(self.player)
        battle = self._check_battle()
        if battle:
            return battle
        if not self.enemy_sprites:
            return FinishScreen(self.display_surface)
        return None


class YSortCameraGroup(pygame.sprite.Group):
	def __init__(self, surface):

		# general setup
		super().__init__()
		self.display_surface = surface
		self.half_width = self.display_surface.get_size()[0] // 2
		self.half_height = self.display_surface.get_size()[1] // 2
		self.offset = pygame.math.Vector2()

	def custom_draw(self,player):
		self.offset.x = player.rect.centerx - self.half_width
		self.offset.y = player.rect.centery - self.half_height

		for sprite in sorted(self.sprites(), key=lambda sprite: (sprite.z, sprite.rect.centery)):
			offset_pos = sprite.rect.topleft - self.offset
			self.display_surface.blit(sprite.image,offset_pos)
