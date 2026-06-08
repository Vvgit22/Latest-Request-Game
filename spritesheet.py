import pygame

class Spritesheet:
    def __init__(self,filename):
        self.filename = filename
        self.sprite_sheet = pygame.image.load(filename).convert()

    def get_sprite():
        pass
