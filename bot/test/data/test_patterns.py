import pytest

from HexBug.data.patterns import PatternOperator


def describe_PatternOperator():
    @pytest.mark.parametrize(
        ["inputs", "outputs", "want_args"],
        [
            (None,     None,      None),
            (None,     "",        None),
            ("",       None,      None),
            ("",       "",        None),
            ("input",  None,      "**__input__ →**"),
            ("input ", None,      "**__input__ →**"),
            (" input", None,      "**__input__ →**"),
            ("a b",    None,      "**__a b__ →**"),
            (None,     "output",  "**→ __output__**"),
            (None,     "output ", "**→ __output__**"),
            (None,     " output", "**→ __output__**"),
            (None,     "a b",     "**→ __a b__**"),
            ("input",  "output",  "**__input__ → __output__**"),
            ("a b",    "c d",     "**__a b__ → __c d__**"),
        ],
    )  # fmt: skip
    def test_args(inputs: str | None, outputs: str | None, want_args: str | None):
        op = PatternOperator(name="", description=None, inputs=inputs, outputs=outputs)
        assert op.args == want_args
