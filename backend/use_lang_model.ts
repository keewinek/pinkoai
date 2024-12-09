import { load_model_init_line } from "./load_model.ts";
import { use_model } from "./use_model.ts";

export function str_to_locations(str: string, model_chars: string)
{
    const char_ids = [];

    for (let i = 0; i < str.length; i++) {
        const char_id = model_chars.indexOf(str[i])
        char_ids.push(char_id);
    }

    const out_locations = [];
    for (let i = 0; i < char_ids.length; i++) {
        out_locations.push(char_ids[i] + (model_chars.length * i));
    }

    return out_locations;
}

export function locations_to_str(locations: number[], model_chars: string)
{
    const char_ids = [];

    for (let i = 0; i < locations.length; i++) {
        const char_id = locations[i] % model_chars.length;
        char_ids.push(char_id);
    }

    let out_str = "";
    for (let i = 0; i < char_ids.length; i++) {
        out_str += model_chars[char_ids[i]];
    }

    return out_str;
}

export function use_language_model(model_name: string, input_str: string)
{
    const model_chars = load_model_init_line(model_name).split(":")[2];
    const starting_locations = str_to_locations(input_str, model_chars);
    
    const final_locations = use_model(model_name, starting_locations);
    const final_str = locations_to_str(final_locations, model_chars);

    console.log(`Input: "${input_str}" Output: "${final_str}"`)
    return final_str;
}

use_language_model("test_model", "AB");