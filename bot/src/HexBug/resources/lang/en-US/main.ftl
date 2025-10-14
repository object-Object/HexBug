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

-parameter_hide-stroke-order =
        hide_stroke_order
-parameter_hide-stroke-order_description =
        Hide the stroke order when rendering the pattern (like for great spells).

# choices

choice_HexBug-utils-discord-visibility-Visibility =
    .PUBLIC =
        public
    .PRIVATE =
        private

choice_HexBug-cogs-app-commands-info-InfoMessage =
    .addons =
        Addons

    .bosnia =
        Bosnia
    .bosnia_text_description =
        Botania.

    .bug-report =
        Bug Report
    .bug-report_text_description =
        Please do not post your bug reports to Discord. Instead, post them to the issue tracker on the mod's GitHub.

        Hex Casting: https://github.com/gamma-delta/HexMod/issues
        PAUCAL: https://github.com/gamma-delta/PAUCAL/issues
        Addons: `/mod`

    .crashlog =
        Crashlog
    .crashlog_text_description =
        You can use a service like [mclo.gs](https://mclo.gs) (preferred) or [Pastebin](https://pastebin.com) to post the crashlog.
        Please do *not* upload it directly to Discord in a message or file.

    .forum =
        Forum
    .forum_text_title =
        petrak@'s mods forum
    .forum_text_description =
        {"["}Join the forum](https://forum.petra-k.at/ucp.php?mode=register) to post/browse cool hexes, ask for help, or chat about petrak@'s mods.

        {"**"}Quick links**
        {"["}General Chat](https://forum.petra-k.at/viewforum.php?f=7)
        {"["}Akashic Records](https://forum.petra-k.at/viewforum.php?f=2)
        {"["}Hexcasting Help](https://forum.petra-k.at/viewforum.php?f=5)
        {"["}Miner's Lung](https://forum.petra-k.at/viewforum.php?f=9)
        {"["}Bliss Mods](https://forum.petra-k.at/viewforum.php?f=10)

    .great-spells =
        Great Spells

    .gtp-itemdrop =
        GTP Item Drop
    .gtp-itemdrop_text_description =
        When someone casts Greater Teleport on themself, each item in their inventory (except for those in their hands and any slots added by mods) has a random chance to drop at their destination.
        For items in the main three inventory rows, the chance is N/10,000. For items in their hotbar, the chance is N/20,000. For items in their armor slots, the chance is N/40,000.
        N is the length of the offset vector supplied to GTP. When the vector is over 32,768 meters long, the spell will fail to teleport the target, but items can still drop.

    .patterns =
        patterns.csv

    .pluralkit =
        PluralKit
    .pluralkit_text_description =
        {"**"}What are all the `[BOT]` messages doing?**
        This is the result of PluralKit, a discord bot for plural people. Plurality is the experience of having more than one mind in one body.

        {"["}PluralKit](https://pluralkit.me/)  |  [More info on plurality](https://morethanone.info/)

    .tools =
        Tools

choice_HexBug-cogs-app-commands-pattern-PatternCheckType =
    .NORMAL =
        Normal
    .PER-WORLD =
        Per-World
    .SPECIAL-PREFIX =
        Special Handler Prefix

# /book

group_book =
        book
    .description =
        Commands for getting links to web book content.

# /book home

command_book-home =
        home
    .description =
        Get a link to a mod's web book.

    .parameter_mod =
        mod
    .parameter_mod_description =
        The name of the mod to look up.

    .parameter_visibility = {-parameter_visibility}
    .parameter_visibility_description = {-parameter_visibility_description}

    .text_categories = Categories
    .text_entries = Entries
    .text_pages = Linkable Pages

# /book category

command_book-category =
        category
    .description =
        Get a link to a category in a mod's web book.

    .parameter_category =
        category
    .parameter_category_description =
        The name of the category to look up.

    .parameter_visibility = {-parameter_visibility}
    .parameter_visibility_description = {-parameter_visibility_description}

    .text_title = [Category] { $name }

# /book entry

command_book-entry =
        entry
    .description =
        Get a link to an entry in a mod's web book.

    .parameter_entry =
        entry
    .parameter_entry_description =
        The name of the entry to look up.

    .parameter_visibility = {-parameter_visibility}
    .parameter_visibility_description = {-parameter_visibility_description}

    .text_title = [Entry] { $name }
    .text_category = Category

# /book page

command_book-page =
        page
    .description =
        Get a link to a page (if it has an anchor) in a mod's web book.

    .parameter_page =
        page
    .parameter_page_description =
        The name of the page to look up.

    .parameter_visibility = {-parameter_visibility}
    .parameter_visibility_description = {-parameter_visibility_description}

    .text_title = [Page] { $title }
    .text_category = Category
    .text_entry = Entry

# /book recipe

command_book-recipe =
        recipe
    .description =
        Get a link to a recipe in a mod's web book.

    .parameter_recipes =
        item
    .parameter_recipes_description =
        The name of the item being crafted.

    .parameter_visibility = {-parameter_visibility}
    .parameter_visibility_description = {-parameter_visibility_description}

    .text_title = [Recipe] { $title }
    .text_category = Category
    .text_entry = Entry
    .text_page = Page

# /changelog

command_changelog =
        changelog
    .description =
        Show HexBug's changelog.

    .parameter_visibility = {-parameter_visibility}
    .parameter_visibility_description = {-parameter_visibility_description}

# /decode

group_decode =
        decode
    .description =
        Decode an iota exported using Reveal.

-decode_contents_description =
        The result of using Reveal on an iota, copied from latest.log.

-decode_flatten-list =
        flatten_list
-decode_flatten-list_description =
        If the iota being decoded is a list, dedent its contents and wrap embedded iotas in <>.

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

    .parameter_flatten-list = {-decode_flatten-list}
    .parameter_flatten-list_description = {-decode_flatten-list_description}

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

    .parameter_flatten-list = {-decode_flatten-list}
    .parameter_flatten-list_description = {-decode_flatten-list_description}

    .parameter_tab-width = {-decode_tab-width}
    .parameter_tab-width_description = {-decode_tab-width_description}

    .parameter_visibility = {-parameter_visibility}
    .parameter_visibility_description = {-parameter_visibility_description}

# /info

command_info =
        info
    .description =
        Show a premade info message.

    .parameter_message =
        message
    .parameter_message_description =
        The name of the message to show.

    .parameter_visibility = {-parameter_visibility}
    .parameter_visibility_description = {-parameter_visibility_description}

    .text_footer-usage-count =
        Times posted: { $count }
    .text_footer-days-since =
        Days since last post: { $days }

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

    .text_loaders = Supported Loaders

    .text_curseforge = CurseForge
    .text_modrinth = Modrinth

    .text_source-github = GitHub
    .text_source-codeberg = Codeberg

    .text_patterns = Patterns

    .text_overloads = Overloads
    .text_overloads-value =
        { $first_party } first-party
        { $third_party } third-party

    .text_special = Special Handlers

    .text_categories = Categories
    .text_entries = Entries
    .text_pages = Linkable Pages
    .text_recipes = Recipes

# /mods

command_mods =
        mods
    .description =
        List all mods supported by HexBug, optionally with filters.

    .parameter_author =
        author
    .parameter_author_description =
        Only show mods authored by this GitHub/Codeberg user.

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

# /palette

command_palette =
        palette
    .description =
        Display one of HexBug's pattern palettes.

    .parameter_palette =
        palette
    .parameter_palette_description =
        The name of the palette to display.

    .parameter_hide-stroke-order = {-parameter_hide-stroke-order}
    .parameter_hide-stroke-order_description = {-parameter_hide-stroke-order_description}

    .parameter_visibility = {-parameter_visibility}
    .parameter_visibility_description = {-parameter_visibility_description}

    .text_rgb = RGB
    .text_hex = Hex
    .text_int = Int

    .text_colors =
        Lines:
        { $colors }

        Overlap:
        { $overlap }

        Per-world:
        { $per_world }

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

    .parameter_hide-stroke-order = {-parameter_hide-stroke-order}
    .parameter_hide-stroke-order_description = {-parameter_hide-stroke-order_description}

    .parameter_visibility = {-parameter_visibility}
    .parameter_visibility_description = {-parameter_visibility_description}

# /pattern check

command_pattern-check =
        check
    .description =
        Check if a pattern already exists in any of the mods supported by HexBug.

    .parameter_signature = {-parameter_signature}
    .parameter_signature_description = {-parameter_signature_description}

    .parameter_pattern-type =
        type
    .parameter_pattern-type_description =
        Treat the pattern as this type when checking for conflicts.

    .parameter_direction = {-parameter_direction}
    .parameter_direction_description = {-parameter_direction_description}

    .parameter_visibility = {-parameter_visibility}
    .parameter_visibility_description = {-parameter_visibility_description}

    .text_title =
        { $conflicts ->
            [0]     No conflicts found.
            [one]   Conflict found!
           *[other] Conflicts found!
        }

    .text_conflict-signature = Signature
    .text_conflict-shape = Shape
    .text_conflict-prefix = Prefix

# /pattern build

command_pattern-build =
        build
    .description =
        Draw a pattern incrementally using directional buttons.

    .parameter_hide-stroke-order = {-parameter_hide-stroke-order}
    .parameter_hide-stroke-order_description = {-parameter_hide-stroke-order_description}

# /patterns

group_patterns =
        patterns
    .description =
        Commands for generating and/or rendering many patterns at once.

# /patterns hex

command_patterns-hex =
        hex
    .description =
        Display a list of patterns.

    .parameter_hex =
        hex
    .parameter_hex_description =
        One or more comma-separated patterns to display. Shorthand is allowed.

    .parameter_visibility = {-parameter_visibility}
    .parameter_visibility_description = {-parameter_visibility_description}

# /patterns number

command_patterns-number =
        number
    .description =
        Generate and display a sequence of patterns to push any rational number to the stack.

    .parameter_number =
        number
    .parameter_number_description =
        The number to generate. May be a decimal or fraction.

    .parameter_visibility = {-parameter_visibility}
    .parameter_visibility_description = {-parameter_visibility_description}

# /per-world-pattern

group_per-world-pattern =
        per-world-pattern
    .description =
        Commands for adding to and querying a per-server list of per-world pattern signatures.

per-world-pattern-added = ✅ **Pattern added.**

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

    .parameter_entry =
        name
    .parameter_entry_description =
        The name of the per-world pattern to look up.

    .parameter_visibility = {-parameter_visibility}
    .parameter_visibility_description = {-parameter_visibility_description}

# /per-world-pattern remove

command_per-world-pattern-remove =
        remove
    .description =
        Remove a per-world pattern from this server's database.

    .parameter_entry =
        name
    .parameter_entry_description =
        The name of the per-world pattern to remove. You can only remove patterns that you added.

    .text_removed = ✅ **Pattern removed.**

# /per-world-pattern-manage

group_per-world-pattern-manage =
        per-world-pattern-manage
    .description =
        Privileged commands for managing this server's list of per-world pattern signatures.

# /per-world-pattern-manage add

command_per-world-pattern-manage-add =
        add
    .description =
        Add a per-world pattern to this server's database that is not in HexBug's registry.

    .parameter_pattern-id =
        id
    .parameter_pattern-id_description =
        The ID of the pattern to add (eg. hexcasting:create_lava).

    .parameter_direction = {-parameter_direction}
    .parameter_direction_description = {-parameter_direction_description}

    .parameter_signature = {-parameter_signature}
    .parameter_signature_description = {-parameter_signature_description}

# /per-world-pattern-manage remove

command_per-world-pattern-manage-remove =
        remove
    .description =
        Remove a per-world pattern from this server's database that was added by another user.

    .parameter_entry =
        name
    .parameter_entry_description =
        The name of the per-world pattern to remove.

    .text_removed = ✅ **Pattern removed.**

# /per-world-pattern-manage remove-all

command_per-world-pattern-manage-remove-all =
        remove-all
    .description =
        Remove all per-world patterns from this server's database.

    .parameter_contributor =
        contributor
    .parameter_contributor_description =
        Only remove patterns that were added by this user.

    .text_confirm-all =
        { $count ->
            [one]   Are you sure you want to remove **{ $count } pattern** from this server?
           *[other] Are you sure you want to remove **{ $count } patterns** from this server?
        }
    .text_confirm-user =
        { $count ->
            [one]   Are you sure you want to remove **{ $count } pattern** added by { $user } from this server?
           *[other] Are you sure you want to remove **{ $count } patterns** added by { $user } from this server?
        }

    .text_cancel = Cancel
    .text_remove =
        { $count ->
            [one]   Remove Pattern
           *[other] Remove Patterns
        }

    .text_cancelled = Cancelled.
    .text_removed =
        { $count ->
            [one]   { $count } pattern removed.
           *[other] { $count } patterns removed.
        }

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

    .text_categories = Categories
    .text_entries = Entries
    .text_pages = Linkable Pages
    .text_recipes = Recipes
