# Adapted from https://github.com/gchpaco/hexdecode

import json
import re
import glob
from hexast import Direction, get_rotated_pattern_segments, PatternRegistry

registry_regex = re.compile(r"PatternRegistry\s*\.\s*mapPattern\s*\(\s*HexPattern\s*\.\s*fromAngles\s*\(\s*\"([aqwed]+)\"\s*,\s*HexDir\s*\.\s*(\w+)\s*\)\s*,\s*modLoc\s*\(\s*\"([\w/]+)\"\s*\).+?(true)?\);", re.M | re.S)
translation_regex = re.compile(r"hexcasting.spell.[a-z]+:(.+)")

def build_registry() -> PatternRegistry:
    registry = PatternRegistry()

    for filename in glob.glob("data/*.json"):
        with open(filename, "r", encoding="utf-8") as file:
            data: dict[str, str] = json.load(file)
            for key, translation in data.items():
                if match := translation_regex.match(key):
                    name = match[1]
                    registry.name_to_translation[name] = translation
    
    for filename in glob.glob("data/*.java"):
        with open(filename, "r", encoding="utf-8") as file:
            for match in registry_regex.finditer(file.read()):
                (pattern, direction, name, is_great) = match.groups()
                if is_great:
                    for segments in get_rotated_pattern_segments(Direction[direction], pattern):
                        registry.great_spells[segments] = name
                else:
                    registry.pattern_to_name[pattern] = name
                translation = registry.name_to_translation.get(name, name) # because Hexal sometimes doesn't have translations
                registry.translation_to_pattern[translation] = (Direction[direction], pattern)

    return registry
