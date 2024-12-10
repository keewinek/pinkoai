import os

def create_empty_model(name, top_pins_count, levels, init_line="MDL:ALL"):
    filepath = f"models/{name}.mdl"

    if os.path.exists(filepath):
        raise Exception(f"Model {name} already exists")
    
    print(f"Creating model {name} with {top_pins_count} pins and {levels} levels...")

    #  create a model file
    with open(filepath, "x") as f:
        f.write(f"{init_line}")
        curr_pins_count = top_pins_count
        for y in range(levels):
            level_raw = ""
            
            for x in range(curr_pins_count):
                level_raw += f"- "

            curr_pins_count += 1

            f.write("\n" + level_raw.rstrip())

    print("Model created.")