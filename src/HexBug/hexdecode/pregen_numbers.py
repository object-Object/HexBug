import json
from pathlib import Path

from HexBug.hexdecode.hex_math import Direction

MAX_PREGEN_NUMBER = 2000

PREGEN_NUMBERS_FILE = (
    f"{Path(__file__).parent.as_posix()}/numbers_{MAX_PREGEN_NUMBER}.json"
)


def load_pregen_numbers():
    with open(PREGEN_NUMBERS_FILE, "r", encoding="utf-8") as f:
        return {int(n): (Direction[d], p) for n, (d, p) in json.load(f).items()}
