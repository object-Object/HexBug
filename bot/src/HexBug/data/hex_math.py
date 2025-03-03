from enum import Enum, auto

from HexBug.utils.pydantic_enum import pydantic_enum


@pydantic_enum
class HexDir(Enum):
    NORTH_EAST = auto()
    EAST = auto()
    SOUTH_EAST = auto()
    SOUTH_WEST = auto()
    WEST = auto()
    NORTH_WEST = auto()
