from enum import Enum

from model_calculate import get_next_locs

class ModType(Enum):
    Empty = 0
    ChanceWay = 1
    Duplicate = 2

class Pin:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.mod_type = ModType.Empty
        self.mod_value = -1

class Level:
    def __init__(self, y, pins):
        self.y = name
        self.pins = pins

class Model:
    def __init__(self,  name):
        self.name = ""
        self.init_line = ""
        self.levels = []

    def get_response(self, start_locs):
        curr_locs = start_locs

        for i in range(len(self.levels)):
            curr_locs = get_next_locs(curr_locs, self.levels[i])

        return curr_locs