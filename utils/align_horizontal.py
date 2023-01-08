from hexdecode.hex_math import Angle, Direction, get_pattern_points


def align_horizontal(direction: Direction, pattern: str) -> tuple[Direction, str]:
    min_height = None
    best_direction = direction

    for option in [direction, direction.rotated(Angle.LEFT), direction.rotated(Angle.RIGHT)]:
        points = list(get_pattern_points(option, pattern))
        height = max(p.r for p in points) - min(p.r for p in points)

        if min_height is None or height < min_height:
            min_height = height
            best_direction = option

    return best_direction, pattern
