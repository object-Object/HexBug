# command/group/parameter name:
#       |------------------------------|

# choice name, command/group/parameter description:
#       |--------------------------------------------------------------------------------------------------|

# common parameters

-parameter_visibility =
        visibility
-parameter_visibility_description =
        Whether the response should be visible to everyone, or just you.

-parameter_direction =
        direction
-parameter_direction_description =
        The starting direction of the pattern (eg. SOUTH_EAST).

-parameter_signature =
        signature
-parameter_signature_description =
        The angle signature of the pattern (eg. deaqq).

# choices

choice_HexBug-utils-discord-visibility-Visibility =
    .PUBLIC =
        public
    .PRIVATE =
        private

# /decode

group_decode =
        decode
    .description =
        Decode an iota exported using Reveal.

-decode_contents_description =
        The result of using Reveal on an iota, copied from latest.log.

-decode_tab-width =
        tab_width
-decode_tab-width_description =
        The amount of spaces per indentation level.

# /decode text

command_decode-text =
        text
    .description =
        Decode an iota exported using Reveal.

    .parameter_text =
        text
    .parameter_text_description = {-decode_contents_description}

    .parameter_tab-width = {-decode_tab-width}
    .parameter_tab-width_description = {-decode_tab-width_description}

    .parameter_visibility = {-parameter_visibility}
    .parameter_visibility_description = {-parameter_visibility_description}

# /decode file

command_decode-file =
        file
    .description =
        Decode the contents of a file containing an iota exported using Reveal.

    .parameter_file =
        file
    .parameter_file_description = {-decode_contents_description}

    .parameter_tab-width = {-decode_tab-width}
    .parameter_tab-width_description = {-decode_tab-width_description}

    .parameter_visibility = {-parameter_visibility}
    .parameter_visibility_description = {-parameter_visibility_description}

# /mod

command_mod =
        mod
    .description =
        Show information and links for mods supported by HexBug.

    .parameter_mod =
        mod
    .parameter_mod_description =
        The name of the mod to look up.

    .parameter_visibility = {-parameter_visibility}
    .parameter_visibility_description = {-parameter_visibility_description}

# /mods

command_mods =
        mods
    .description =
        List all mods supported by HexBug, optionally with filters.

    .parameter_author =
        author
    .parameter_author_description =
        Only show mods authored by this GitHub user.

    .parameter_modloader =
        modloader
    .parameter_modloader_description =
        Only show mods with support for this modloader.

    .parameter_visibility = {-parameter_visibility}
    .parameter_visibility_description = {-parameter_visibility_description}

    .text_title =
        { $modloader ->
            [None]  Loaded Mods
           *[other] Loaded Mods ({ $modloader })
        }

    .text_footer-normal =
        Count: { $mods }
    .text_footer-filtered =
        Count: { $mods }/{ $total }

    .text_no-mods-found =
        ⚠️ No mods found with these filters.

# /pattern

group_pattern =
        pattern
    .description =
        Commands for looking up and rendering patterns.

# /pattern name

command_pattern-name =
        name
    .description =
        Look up a pattern by name.

    .parameter_info =
        name
    .parameter_info_description =
        The name of the pattern to look up.

    .parameter_visibility = {-parameter_visibility}
    .parameter_visibility_description = {-parameter_visibility_description}

# /pattern special

command_pattern-special =
        special
    .description =
        Generate a pattern for a special handler (eg. Bookkeeper's Gambit).

    .parameter_info =
        name
    .parameter_info_description =
        The name of the pattern to generate.

    .parameter_value =
        value
    .parameter_value_description =
        The special handler value (eg. v-vv---v). The format depends on the pattern being generated.

    .parameter_visibility = {-parameter_visibility}
    .parameter_visibility_description = {-parameter_visibility_description}

# /pattern raw

command_pattern-raw =
        raw
    .description =
        Generate a pattern from its angle signature.

    .parameter_direction = {-parameter_direction}
    .parameter_direction_description = {-parameter_direction_description}

    .parameter_signature = {-parameter_signature}
    .parameter_signature_description = {-parameter_signature_description}

    .parameter_hide-stroke-order =
        hide_stroke_order
    .parameter_hide-stroke-order_description =
        If true, hide the stroke order when rendering the pattern (like for great spells).

    .parameter_visibility = {-parameter_visibility}
    .parameter_visibility_description = {-parameter_visibility_description}

# /pattern check

command_pattern-check =
        check
    .description =
        Check if a pattern already exists in any of the mods supported by HexBug.

    .parameter_signature = {-parameter_signature}
    .parameter_signature_description = {-parameter_signature_description}

    .parameter_is-per-world =
        is_per_world
    .parameter_is-per-world_description =
        If true, also check for non-per-world patterns with the same shape but a different stroke order.

    .parameter_visibility = {-parameter_visibility}
    .parameter_visibility_description = {-parameter_visibility_description}

    .text_title =
        { $conflicts ->
            [0]     No conflicts found.
            [one]   Conflict found!
           *[other] Conflicts found!
        }

# /per-world-pattern

group_per-world-pattern =
        per-world-pattern
    .description =
        Commands for managing a per-server list of per-world pattern signatures.

per-world-pattern-contributor = Added by { $name }

# /per-world-pattern add

command_per-world-pattern-add =
        add
    .description =
        Add a per-world pattern to this server's database.

    .parameter_direction = {-parameter_direction}
    .parameter_direction_description = {-parameter_direction_description}

    .parameter_signature = {-parameter_signature}
    .parameter_signature_description = {-parameter_signature_description}

# /per-world-pattern list

command_per-world-pattern-list =
        list
    .description =
        List the per-world patterns in this server's database.

    .parameter_contributor =
        contributor
    .parameter_contributor_description =
        Only list patterns that were added by this user.

    .parameter_visibility = {-parameter_visibility}
    .parameter_visibility_description = {-parameter_visibility_description}

    .text_title = Per-World Patterns

    .text_no-patterns-found = ⚠️ No patterns found.

# /per-world-pattern name

command_per-world-pattern-name =
        name
    .description =
        Look up a per-world pattern in this server's database by name.

    .parameter_info =
        name
    .parameter_info_description =
        The name of the per-world pattern to look up.

    .parameter_visibility = {-parameter_visibility}
    .parameter_visibility_description = {-parameter_visibility_description}

# /status

command_status =
        status
    .description =
        Show information about HexBug.

    .parameter_visibility = {-parameter_visibility}
    .parameter_visibility_description = {-parameter_visibility_description}

    .text_title = HexBug Status

    .text_commit = Deployed commit
    .text_commit-unknown = Unknown

    .text_deployment-time = Deployment time
    .text_deployment-time-unknown = Unknown

    .text_uptime = Uptime

    .text_installs = Installs
    .text_installs-value =
        { $servers ->
            [one]   1 server
           *[other] { $servers } servers
        }
        { $users ->
            [one]   1 individual user
           *[other] { $users } individual users
        }

    .text_mods = Mods

    .text_patterns = Patterns
