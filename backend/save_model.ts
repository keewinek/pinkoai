import { model } from "./backend_interfaces/model.ts";
import { ModifierType } from "./backend_interfaces/pin.ts";

export function get_model_raw(model: model)
{
    let model_raw = `${model.init_line}\n`;

    for (let i = 0; i < model.levels.length; i++) {
        const level = model.levels[i];
        let level_raw = "";

        for (let j = 0; j < level.pins.length; j++) {
            const pin = level.pins[j];

            if (pin.modifier_type == ModifierType.Empty) {
                level_raw += "- "
            }
            else if (pin.modifier_type == ModifierType.Duplicate) {
                level_raw += "D "
            }
            else if (pin.modifier_type == ModifierType.RandomWay) {
                level_raw += pin.modifier_value.toString() + " "
            }
        }

        level_raw = level_raw.trim();
        model_raw += level_raw + "\n";
    }

    if (model_raw[model_raw.length - 1] == "\n") {
        model_raw = model_raw.slice(0, -1);
    }

    return model_raw;
}

export function save_model(model: model)
{
    const model_raw = get_model_raw(model);
    Deno.writeTextFileSync(`models/${model.name}.mdl`, model_raw);
}

export function update_model_file(model: model) {
    save_model(model);
}