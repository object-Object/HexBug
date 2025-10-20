from typing import Any

from hexdoc.core import ResourceLocation


class DuplicatePatternError(ValueError):
    def __init__(self, field: str, value: Any, *pattern_ids: ResourceLocation):
        ids = ", ".join(str(pattern_id) for pattern_id in pattern_ids)
        super().__init__(f"Multiple patterns found with same {field} ({value}): {ids}")
