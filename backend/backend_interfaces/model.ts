import { level } from "./level.ts";

export interface model
{
    name: string;
    init_line: string;
    levels: level[];
}