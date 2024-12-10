from interfaces.model_like import *
from rng import *

# Get next balls locations at certain level with pins
def get_next_locs(curr_locs, level):
    next_locs = []

    for x in curr_locs:
        pin = level.pins[x]

        create_pin_left = False
        create_pin_right = False

        if (pin.mod_type == ModType.Duplicate):
            create_pin_left = True
            create_pin_right = True
        elif (pin.mod_type == ModType.Empty):
            if (get_chance() < 50):
                create_pin_right = True
            else:
                create_pin_left = True
        elif (pin.mod_type == ModType.ChanceWay):
            if (get_chance() < pin.mod_value):
                create_pin_right = True
            else:
                create_pin_left = True
        else:
            throw("Unknown mod type")
        
        # Handle balls collisions
        if (next_locs.count(x) > 0 and create_pin_left):
            create_pin_left = False
            create_pin_right = True

        if (create_pin_left):
            next_locs.append(x)
        if (create_pin_right):
            next_locs.append(x + 1)
        
    return next_locs