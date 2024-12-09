import { level } from "./backend_interfaces/level.ts";
import { model } from "./backend_interfaces/model.ts";
import { ModifierType } from "./backend_interfaces/pin.ts";
import { load_model_by_name } from "./load_model.ts";
import { get_chance } from "./rng.ts";

function calculate_next_locations(current_locations: number[], level: level)
{
    const next_locations = new Set<number>();

    for (let i = 0; i < current_locations.length; i++) {
        const x = current_locations[i];
        const pin = level.pins[x];

        let create_pin_left = false;
        let create_pin_right = false;

        if (pin.modifier_type == ModifierType.Duplicate) {
            create_pin_left = true;
            create_pin_right = true;
        }
        else if (pin.modifier_type == ModifierType.Empty) {
            if (get_chance() < 50) { create_pin_right = true; } // Szansa 50%, na to, że przebijamy i idziemy w prawo
            else { create_pin_left = true; } 
        }
        else if (pin.modifier_type == ModifierType.RandomWay) {
            const chance = get_chance();
            if (chance < pin.modifier_value) { create_pin_right = true; }
            else { create_pin_left = true; }
        }
        else {
            throw new Error("Unknown pin modifier type.");
        }
        
        // Handle ball collisions
        if (next_locations.has(x) && create_pin_left) {
            create_pin_left = false;
            create_pin_right = true;
        }

        // Add the ball locations
        if (create_pin_left) {
            next_locations.add(x);
        }

        if (create_pin_right) {
            next_locations.add(x + 1);
        }
    }

    return Array.from(next_locations);
}

export function use_model(model_name: string, start_locations: number[]) {
    const model: model = load_model_by_name(model_name);
    let current_locations = start_locations;

    for (let y = 0; y < model.levels.length; y++) {
        const level = model.levels[y];
        current_locations = calculate_next_locations(current_locations, level);
        console.log(`Using model.. ${y}: Loc:${current_locations}`)
    }

    return current_locations;
}

use_model("manual", [0, 2]);