import pygame
from default import *
from entity import Entity


class Enemy(Entity):
    def __init__(self, pos, groups, obstacle_sprites, enemy_type='ghost'):
        super().__init__(groups)
        self.obstacle_sprites = obstacle_sprites
        self.enemy_type = enemy_type

        data = ENEMY_DATA[enemy_type]
        self.hp = data['hp']
        self.reps = data.get('reps', data['hp'])
        self.sets = data.get('sets', 1)
        self.exercise = data['exercise']
        self.animation_speed = data['animation_speed']
        self.frames = [pygame.image.load(f'graphics/{enemy_type}{i}.png').convert_alpha() for i in range(1, data['frames'] + 1)]
        self.frame_index = 0
        self.image = self.frames[0]
        self.rect = self.image.get_rect(topleft=pos)
        self.hitbox = self.rect.inflate(0, -2)

    def animate(self):
        self.frame_index = (self.frame_index + self.animation_speed) % len(self.frames)
        self.image = self.frames[int(self.frame_index)]

    def update(self):
        self.animate()
