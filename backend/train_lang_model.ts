import {distance, closest} from 'https://deno.land/x/fastest_levenshtein/mod.ts'
import { training_pair } from "./backend_interfaces/training_pair.ts";
import { load_model_by_name } from "./load_model.ts";
import { save_model } from "./save_model.ts";

const training_attempts_per_pair = 100;
const parameters_to_tweak = 1000;
const training_pairs: training_pair[] = [
    {in: "A", out: "BC"},
    {in: "CA", out: "CBA"}
]

export function train_model(model_name: string) {
    const model = load_model_by_name(model_name);

    // TODO: for parameters_to_tweak times pick a random parameter and see if its worth changing (do 100 attempts to calculate the avg outcome distance)

    save_model(model);
}

train_model("test_model")