from io import BytesIO
import math
import matplotlib.pyplot as plt
from hexast import Direction, Coord, Angle
from hex_interpreter.hex_draw import plot_intersect

def get_points(direction: Direction, pattern: str) -> list[Coord]:
    compass = direction
    cursor = compass.as_delta()

    points = [Coord.origin(), cursor]

    for c in pattern:
        compass = compass.rotated(Angle[c])
        cursor += compass
        points.append(cursor)

    return points

def generate_image(direction: Direction, pattern: str, line_scale: float, arrow_scale: float) -> BytesIO:
    points = get_points(direction, pattern)
    x_vals: list[float] = []
    y_vals: list[float] = []
    for point in points:
        (x, y) = point.pixel(1)
        x_vals.append(x)
        y_vals.append(-y)

    width = max(x_vals) - min(x_vals)
    height = max(y_vals) - min(y_vals)
    max_width = max(width, height, 1.25)
    scale = line_scale/math.log(max_width, 1.5) + 1.1

    fig = plt.figure(figsize=(4,4))
    ax = fig.add_axes([0,0,1,1])
    ax.set_aspect("equal")
    ax.axis("off")

    settings = {
        "intersect_colors": [
            "#ff6bff",
            "#a81ee3",
            "#6490ed",
            "#b189c7",
        ],
        "arrow_scale": arrow_scale,
    }

    plt.plot(
        x_vals[1]/2.15,
        y_vals[1]/2.15,
        color=settings["intersect_colors"][0],
        marker=(3, 0, (direction.angle_from(Direction.EAST).deg - 90)),
        ms=2.6*arrow_scale*scale
    )
    plot_intersect(x_vals, y_vals, scale, len(x_vals)-1, settings)

    buf = BytesIO()
    fig.savefig(buf, format="jpg")
    buf.seek(0)
    plt.close(fig)
    return buf
