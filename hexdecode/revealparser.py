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

from __future__ import annotations

from lark.exceptions import LarkError
from lark.lark import Lark
from lark.visitors import Transformer

from hexdecode import hexast

parser = Lark(
    """
start: iota*

iota: "[" [iota ("," iota)*] "]"                -> list
    | "(" ( NUMBER "," NUMBER "," NUMBER ) ")"  -> vector
    | "HexPattern" "(" ( DIRECTION TURNS? ) ")" -> pattern
    | "NULL"                                    -> null
    | NUMBER                                    -> literal
    | UNKNOWN                                   -> unknown

TURNS: ("a"|"q"|"w"|"e"|"d")+
UNKNOWN: DIRECTION

%import common.CNAME -> DIRECTION
%import common.SIGNED_FLOAT -> NUMBER
%import common.WS
%ignore WS
"""
)


class ToAST(Transformer):
    def vector(self, args) -> hexast.Vector:
        return hexast.Vector(args[0], args[1], args[2])

    def list(self, iotas):
        return [i for i in iotas if i is not None]

    def null(self, _arguments):
        return hexast.Null()

    def literal(self, numbers):
        return numbers[0]

    def unknown(self, arguments):
        return arguments[0]

    def pattern(self, args):
        initial_direction, *maybe_turns = args
        turns = maybe_turns[0] if len(maybe_turns) > 0 else ""
        return hexast.UnknownPattern(initial_direction, turns)

    def DIRECTION(self, string):
        return hexast.Direction[string]

    def UNKNOWN(self, strings):
        return hexast.Unknown("".join(strings))

    def NUMBER(self, number):
        return hexast.NumberConstant("".join(number))

    def TURNS(self, turns):
        return "".join(turns)

    def start(self, iotas):
        return iotas


def parse(text):
    try:
        tree = parser.parse(text)
        result = ToAST().transform(tree)
    except LarkError:
        return
    for child in result:
        yield child
