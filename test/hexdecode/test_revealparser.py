from HexBug.hexdecode.revealparser import parser


def test_parser():
    text = "[]"
    print(parser.parse(text).pretty())
