import { location } from "./location.ts";

export enum ModifierType
{
    Empty,
    RandomWay,
    Duplicate
}

export interface pin
{
    location: location;
    modifier_type: ModifierType;
    modifier_value: number;
}