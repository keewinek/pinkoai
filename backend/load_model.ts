import { model } from "./backend_interfaces/model.ts";
import { level } from "./backend_interfaces/level.ts";
import { pin } from "./backend_interfaces/pin.ts";
import { ModifierType } from "./backend_interfaces/pin.ts";

export function get_model_raw(filepath: string) {
    const model_raw = Deno.readTextFileSync(filepath);
    return model_raw;
}

function get_model_object(model_raw: string, name: string) {
    const model: model = {
        name: name,
        levels: []
    }

    const model_raw_levels = model_raw.split("\n");

    for (let y = 0; y < model_raw_levels.length; y++) {
        const level: level = {y: y, pins:[]};

        const level_raw = model_raw_levels[y];
        const level_raw_pins = level_raw.split(" ");

        for (let x = 0; x < level_raw_pins.length; x++) {
            const pin_raw = level_raw_pins[x];
            let pin_modifier_type = ModifierType.RandomWay;
            let pin_modifier_value = -1;

            if (pin_raw == "D") {
                pin_modifier_type = ModifierType.Duplicate;
            }
            else if (pin_raw == "-" || pin_raw == "E") {
                pin_modifier_type = ModifierType.Empty;
            }
            else {
                pin_modifier_value = parseInt(pin_raw);
            }

            const pin: pin = {
                location: {x: x, y: y},
                modifier_type: pin_modifier_type,
                modifier_value: pin_modifier_value
            }

            level.pins.push(pin);
        }

        model.levels.push(level);
    }

    return model;
}

export function load_model_by_name(name: string) {
    const model_filepath = `./models/${name}.mdl`;

    console.log(`Loading model: ${model_filepath}..`);

    const model_raw = get_model_raw(`./models/${name}.mdl`);
    const model = get_model_object(model_raw, name);

    console.log(`Model ${name} loaded.`);

    return model;
}