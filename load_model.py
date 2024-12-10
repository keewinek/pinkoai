from interfaces.model_like import *
from model import *

def get_file_raw(filepath):
    with open(filepath, 'r') as f:
        return f.read()

def get_model_from_raw(model_raw, name):
    model = Model(name)
    lines = model_raw.split('\n')

    if (not lines[0].startswith("MDL")):
        throw(f"Invalid model file format model: ${name}.")
    
    model.init_line = lines[0]

    for i in range(1, len(lines)):
        line = lines[i]
        level = Level(i - 1, [])
        
        raw_pins = line.split(' ')
        for j in range(len(raw_pins)):
            pin = Pin(j, i - 1)
            pin_raw = raw_pins[j]

            if pin_raw == "":
                continue

            if pin_raw.startswith("E") or pin_raw == "-":
                pin.mod_type = ModType.Empty
            elif pin_raw.startswith("D"):
                pin.mod_type = ModType.Duplicate
            else:
                pin.mod_type = ModType.ChanceWay
                pin.mod_value = pin_raw

            level.pins.append(pin)

        model.levels.append(level)

    return model

def get_model_from_file(filepath):
    return get_model_from_raw(get_file_raw(filepath), filepath.split('/')[-1].split('.')[0])

def get_model_by_name(name):
    return get_model_from_file(f"models/{name}.mdl")