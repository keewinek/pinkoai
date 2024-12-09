function get_random_int(min: number, max: number): number {
    return Math.floor(Math.random() * (max - min + 1)) + min;
}

// get a number from 0 to 100
export function get_chance()
{
    const number: number = get_random_int(0, 100);
    return number;
}