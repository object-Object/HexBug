# "glue" script to allow generating number literals live with a timeout
# i'm pretty sure this is actually the best way to do this, which is awful

import sys

from hexnumgen import AStarOptions, generate_number_pattern

if __name__ == "__main__":
    if len(sys.argv) not in [2, 3]:
        sys.exit(1)
    numer = sys.argv[1]
    denom = sys.argv[2] if len(sys.argv) == 3 else 1

    result = generate_number_pattern(
        (int(numer), int(denom)),
        trim_larger=False,
        allow_fractions=True,
        options=AStarOptions(),
    )
    if result is None:
        sys.exit(1)

    print(result.direction, result.pattern)
