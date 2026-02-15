from typing import Sequence

# https://github.com/object-Object/hexxy.media/blob/9cbd4a00538c958e98106e321dcf2d51da97a48c/src/hexxy_media/api/utils/lehmer.py


def swizzle(*, before: Sequence[str], after: Sequence[str]):
    """
    Given a target stack state, compute the Lehmer code (Swindler's input) which
    transforms the given start state to the target state. Stack states are written
    bottom to top, left to right.
    """

    n = len(after)
    if n > len(before):
        raise ValueError("too few stack elems")

    before = list(before)[-n:]

    stack = [1]
    for i in range(1, n):
        stack.append(stack[-1] * i)

    count = 0
    for val in after:
        ix = before.index(val)
        count += stack.pop() * ix
        del before[ix]

    return count
