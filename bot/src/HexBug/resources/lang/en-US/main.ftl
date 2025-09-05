# command/group/parameter name:
#       |------------------------------|

# command/group/parameter description:
#       |--------------------------------------------------------------------------------------------------|

# common parameters

-parameter_visibility_description =
        Whether the message should be visible to everyone, or just you.

# /pattern check

command_pattern-check =
    .text_title =
        { $conflicts ->
            [0] No conflicts found.
            [one] Conflict found!
            *[other] Conflicts found!
        }

# /status

command_status =
        status
    .description =
        Show information about HexBug.

    .parameter_visibility =
        visibility
    .parameter_visibility_description =
        {-parameter_visibility_description}

    .text_title = HexBug Status

    .text_commit = Deployed commit
    .text_commit-unknown = Unknown

    .text_deployment-time = Deployment time
    .text_deployment-time-unknown = Unknown

    .text_uptime = Uptime

    .text_installs = Installs
    .text_installs-value =
        { $servers ->
            [one] 1 server
            *[other] { $servers } servers
        }
        { $users ->
            [one] 1 individual user
            *[other] { $users } individual users
        }

    .text_mods = Mods

    .text_patterns = Patterns
