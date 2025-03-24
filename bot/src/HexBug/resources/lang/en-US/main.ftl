# command descriptions: {command}_description
#   |--------------------------------------------------------------------------------------------------|

# parameter descriptions: {command}_parameter-description_{parameter}
#   |--------------------------------------------------------------------------------------------------|

# common parameters

-parameter-description_visibility =
    Whether the message should be visible to everyone, or just you.

# /pattern check

pattern-check_text_title =
    { $conflicts ->
        [0] No conflicts found.
        [one] Conflict found!
        *[other] Conflicts found!
    }
