"""Core OpenSlots module"""


class Reel(object):
    def __init__(self, symbols, window=3):
        self.window = window
        self.symbols = symbols


class Game(object):
    def __init__(self, reels, paytable):
        self.reels = reels
        self.paytable = paytable