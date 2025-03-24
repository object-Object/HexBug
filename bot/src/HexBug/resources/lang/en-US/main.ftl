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

# /status

status_description =
    Show information about HexBug.

status_parameter-description_visibility =
    {-parameter-description_visibility}

status_text_title =
    HexBug Status

status_text_commit =
    Deployed commit

status_text_commit_unknown =
    Unknown

status_text_deployment-time =
    Deployment time

status_text_deployment-time_unknown =
    Unknown

status_text_uptime =
    Uptime

status_text_installs =
    Install count

status_text_installs_value =
    { $servers ->
        [one] 1 server
        *[other] { $servers } servers
    }
    { $users ->
        [one] 1 individual user
        *[other] { $users } individual users
    }

status_text_commands =
    Commands

status_text_mods =
    Mods

status_text_patterns =
    Patterns

status_text_special-handlers =
    Special handlers
