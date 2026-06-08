import pygame 
from default import *
from random import randint 

class Tile(pygame.sprite.Sprite):
    def __init__(self,pos,groups,type):
        super().__init__(groups)
        if type == 'x':
            self.image = pygame.image.load("graphics/wall-tile.png")
        elif type == ' ':
            num = str(randint(1,4))
            self.image = pygame.image.load(f"graphics/floor-{num}.png")
        self.z = 0 if type == ' ' else 1
        self.rect = self.image.get_rect(topleft = pos)
        self.hitbox = self.rect.inflate(0,-2)