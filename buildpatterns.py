"""
MIT License

Copyright (c) 2022 Graham Hughes, object-Object

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

https://github.com/gchpaco/hexdecode
"""

import json
import re
import glob
from hexast import Direction, get_rotated_pattern_segments, PatternRegistry

registry_regex = re.compile(r"PatternRegistry\s*\.\s*mapPattern\s*\(\s*HexPattern\s*\.\s*fromAngles\s*\(\s*\"([aqwed]+)\"\s*,\s*HexDir\s*\.\s*(\w+)\s*\)\s*,\s*modLoc\s*\(\s*\"([\w/]+)\"\s*\).+?(true)?\);", re.M | re.S)
translation_regex = re.compile(r"hexcasting.spell.[a-z]+:(.+)")

lang_files = [
    "HexMod/Common/src/main/resources/assets/hexcasting/lang/en_us.json",
    "Hexal/Common/src/main/resources/assets/hexal/lang/en_us.json",
]

pattern_files = [
    "HexMod/Common/src/main/java/at/petrak/hexcasting/common/casting/RegisterPatterns.java",
    "HexMod/Common/src/main/java/at/petrak/hexcasting/interop/pehkui/PehkuiInterop.java",
    "HexMod/Fabric/src/main/java/at/petrak/hexcasting/fabric/interop/gravity/GravityApiInterop.java",
    "Hexal/Common/src/main/java/ram/talia/hexal/common/casting/RegisterPatterns.java",
]

def build_registry() -> PatternRegistry:
    registry = PatternRegistry()

    # read the translations
    for filename in lang_files:
        with open(filename, "r", encoding="utf-8") as file:
            data: dict[str, str] = json.load(file)
            for key, translation in data.items():
                if match := translation_regex.match(key):
                    name = match[1]
                    registry.name_to_translation[name] = translation.replace(": %s", "") # because the new built in decoding interferes with this
    
    # read the patterns
    for filename in pattern_files:
        with open(filename, "r", encoding="utf-8") as file:
            for match in registry_regex.finditer(file.read()):
                (pattern, direction, name, is_great) = match.groups()
                if is_great:
                    for segments in get_rotated_pattern_segments(Direction[direction], pattern):
                        registry.great_spells[segments] = name
                else:
                    registry.pattern_to_name[pattern] = name
                translation = registry.name_to_translation.get(name, name) # because Hexal sometimes doesn't have translations
                registry.translation_to_pattern[translation] = (Direction[direction], pattern, bool(is_great))

    return registry
