from enum import Enum

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

    def __str__(self):
        return f"Pin: {self.x}, {self.y}, {self.mod_type}, {self.mod_value}"

class Level:
    def __init__(self, y, pins):
        self.y = y
        self.pins = pins
    
    def __str__(self):
        return f"Level: {self.y}\n{self.pins}"