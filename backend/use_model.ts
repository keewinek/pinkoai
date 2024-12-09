import { level } from "./backend_interfaces/level.ts";
import { model } from "./backend_interfaces/model.ts";
import { ModifierType } from "./backend_interfaces/pin.ts";
import { load_model_by_name } from "./load_model.ts";

function calculate_next_locations(current_locations: number[], level: level)
{
    const next_locations: number[] = [];

    for (let i = 0; i < current_locations.length; i++) {
        const x = current_locations[i];
        const pin = level.pins[x];

        if (pin.modifier_type == ModifierType.Empty) {
            next_locations.push(x);
        }
    }

    return next_locations;
}

export function use_model(model_name: string, start_locations: number[] = []) {
    const model: model = load_model_by_name(model_name);

}

use_model("manual", [0]);