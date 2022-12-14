import fileinput

from hexdecode import revealparser
from hexdecode.buildpatterns import build_registry
from hexdecode.hexast import massage_raw_pattern_list

registry = build_registry()

for line in fileinput.input(files=[], encoding="utf-8"):
    level = 0
    for pattern in revealparser.parse(line):
        for iota in massage_raw_pattern_list(pattern, registry):
            level = iota.preadjust(level)
            print(iota.print(level, True, registry))
            level = iota.postadjust(level)
