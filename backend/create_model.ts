import {existsSync} from "https://deno.land/std/fs/mod.ts";

export function create_empty_model(name: string, top_pins: number, levels: number, init_line: string="MDL:ALL")
{
    const filepath = `./models/${name}.mdl`;

    // if file already exists
    if (existsSync(filepath))
    {
        console.log(`Model ${name} already exists.`);
        return;
    }

    console.log(`Creating empty model: ${filepath} with ${levels} levels and ${top_pins}..`);

    Deno.writeTextFileSync(filepath, "");
    Deno.writeTextFileSync(filepath, init_line, { append: true });

    let current_pin_count = top_pins;
    for (let i = 0; i < levels; i++)
    {
        let level_str = "";

        for (let j = 0; j < current_pin_count; j++) {
            level_str += "- ";
        }

        level_str = level_str.trimEnd();
        Deno.writeTextFileSync(filepath, "\n" + level_str, { append: true });
        current_pin_count += 1;
    }

    console.log(`Model ${name} created.`);
}

export function create_empty_language_model(name: string, characters: string, max_chars: number, levels: number,)
{
    const init_line = `MDL:LANG:${characters}`;
    const top_pins = characters.length * max_chars;
    create_empty_model(name, top_pins, levels, init_line);
}

create_empty_language_model("full_alphabet", "AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuWwXxYyZz0123456789., ", 100, 200);