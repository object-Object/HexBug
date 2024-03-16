from HexBug.hexdecode.hex_math import Angle, Direction


def parse_numerical_reflection(pattern: str) -> float | None:
    match pattern[:4]:
        case "aqaa":
            sign = 1
        case "dedd":
            sign = -1
        case _:
            return None

    accumulator = 0
    for c in pattern[4:]:
        match c:
            case "w":
                accumulator += 1
            case "q":
                accumulator += 5
            case "e":
                accumulator += 10
            case "a":
                accumulator *= 2
            case "d":
                accumulator /= 2

    return sign * accumulator


# TODO: make less gross
def parse_bookkeeper(starting_direction: Direction, pattern: str) -> str | None:
    if not pattern:
        return "-"

    directions = _get_pattern_directions(starting_direction, pattern)
    flat_direction = (
        starting_direction.rotated(Angle.LEFT)
        if pattern[0] == "a"
        else starting_direction
    )
    mask = ""
    skip = False
    for index, direction in enumerate(directions):
        if skip:
            skip = False
            continue
        angle = direction.angle_from(flat_direction)
        if angle == Angle.FORWARD:
            mask += "-"
            continue
        if index >= len(directions) - 1:
            return None
        angle2 = directions[index + 1].angle_from(flat_direction)
        if angle == Angle.RIGHT and angle2 == Angle.LEFT:
            mask += "v"
            skip = True
            continue
        return None
    return mask


def _get_pattern_directions(starting_direction: Direction, pattern: str):
    directions = [starting_direction]
    for c in pattern:
        directions.append(directions[-1].rotated(c))
    return directions
