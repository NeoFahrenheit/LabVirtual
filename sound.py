"""
Autor: Leandro Monteiro
Arquivo responsável pela classe de gerenciamento de som.
sound.py
"""

# Desabilita a mensagem de boas-vinas do pygame no console.
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

import pygame

class SoundManager():
    def __init__(self, parent):
        self.parent = parent
        pygame.init()
        pygame.mixer.init()
        pygame.mixer.set_num_channels(8)

        self.pumpMixer = pygame.mixer.Channel(5)
        self.waterMixer = pygame.mixer.Channel(6)

        self.pumpSound = pygame.mixer.Sound('sounds/water_pump.wav')
        self.waterSound = pygame.mixer.Sound('sounds/water_flowing.wav')

    def SoundPlayback(self, key, state):
        ''' Toca ou para o som. '''

        if key == 'rpm':
            if state:
                if not self.pumpMixer.get_busy():
                    self.pumpMixer.play(self.pumpSound, loops=-1)
            else:
                self.pumpMixer.stop()

        elif key == 'abertura':
            if state:
                if not self.waterMixer.get_busy():
                    self.waterMixer.play(self.waterSound, loops=-1)
            else:
                self.waterMixer.stop()

    def SoundVolume(self, volume):
        ''' Muda o volume. '''

        self.pumpMixer.set_volume(volume / 5)   # Barulho do motor é muito alto.
        self.waterMixer.set_volume(volume)