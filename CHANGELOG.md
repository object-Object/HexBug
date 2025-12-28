# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and [Pydantic's HISTORY.md](https://github.com/pydantic/pydantic/blob/main/HISTORY.md), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [UNRELEASED]

### Fixed

- Fixed HexxyPlanes description.
- Fixed an internal error in `/pattern build` when attempting to undo the first line drawn.
- Fixed `/pattern build` defaulting to `EAST` instead of an empty grid.
- Fixed `/pattern build` not deleting the original message when clicking the ✅ button.

### Mods Updated

- HexxyPlanes: 0.2.1+1.20.1
- Yet Another Hex Addon: 0.2.0

## `2.7.0` - 2025-12-20

### Changed

- Added an optional `show_signatures` argument to `/patterns hex` (default `False`) to control whether the angle signatures in the footer are shown.
- Added the ability to specify a starting pattern for `/pattern build`.

### Fixed

- Fixed `/patterns hex` not hiding the stroke order of per-world patterns.

### Mods Added

- HexxyPlanes: 0.2.0+1.20.1
- Yet Another Hex Addon: 0.1.0

### Mods Updated

- Dynamic Trees - Hexcasting: 1.0.2
- HexParse: 1.6.0
- HexThings: 0.1.5+1.20.1
- Lapisworks: 1.5.7

## `2.6.0` - 2025-11-25

### Added

- Added support for regular expressions to `/pattern check`.

### Mods Added

- HexThings: 0.1.4+1.20.1
- Hexic (again): 1.4.6

### Mods Updated

- Hex Casting: 0.11.3
- HexFlow: 0.3.3
- HexOverpowered: 0.10.1
- mediatransport: 1.1.1+1.20.1

## `2.5.1` - 2025-11-13

### Changed

- Added a length limit of 512 characters for pattern angle signatures.

### Fixed

- Fixed older versions of the Book of Hexxy being overwritten by redirect loops.

### Removed

- Removed Hexic due to GPL license, and because malicious code was included in the mod.

### Mods Updated

- Hexal: 0.3.1
- HexDebug: 0.8.0+1.20.1
- HexParse: 1.5.0

## `2.5.0` - 2025-10-23

### Added

- Added a new command `/book search` to perform full-text search across all mod books using [Tantivy](https://github.com/quickwit-oss/tantivy)'s [query language](https://docs.rs/tantivy/latest/tantivy/query/struct.QueryParser.html).

### Fixed

- Added a missing translation for the Recipes header in `/book home`.

### Mods Updated

- Hexic: 1.4.2

## `2.4.1` - 2025-10-20

### Fixed

- Hotfix: fix incorrect dependencies on PyPI for `HexBug-data`, and clarify installation instructions.

## `2.4.0` - 2025-10-20

### Changed

- Moved HexBug's registry classes into a standalone Python package: https://pypi.org/project/HexBug-data
- The following files are now generated in the Book of Hexxy:
  - `registry.json`
  - Wheel, `constraints.txt`, and `pylock.toml` for `HexBug-data`

### Fixed

- Fixed a bug where indented changelog items were displayed incorrectly in `/changelog`.

### Mods Updated

- Hexal: 0.3.0
- Hexic: 1.4.1
- Lapisworks: 1.5.6.9
- mediatransport: 1.1.0+1.20.1

## `2.3.0` - 2025-10-14

### Changed

- Added the ability to check for special handler prefix conflicts with `/pattern check`.
- Added an optional `direction` argument to `/pattern check`.
- `/pattern check` now lists conflicts separately by reason.
- Changed capitalization of `visibility` option.
- The combined web book at https://book.hexxy.media is now released along with HexBug, instead of just always reflecting the latest commit.

### Mods Added

- Hexic: 1.3.4

### Mods Updated

- mediatransport: 1.0.2+1.20.1

## `2.2.0` - 2025-10-10

### Added

- Added a new command `/changelog` to show HexBug's changelog.

### Mods Added

- Hex Trace: 0.1.0+1.20.1
- mediatransport: 1.0.1+1.20.1

### Mods Updated

- Hexal: 0.3.0-4 @ 16425bdc
- Hexical: 2.0.0 @ e0d7ef97

## `2.1.0` - 2025-10-07

### Added

- Added a new option `flatten_list` to `/decode`. If enabled (the default) and the iota being decoded is a list, its contents are dedented and any embedded iotas are wrapped in `<>`, like in `.hexpattern`.

### Changed

- Added more shorthand names to a few patterns in `/patterns hex`.
- `/patterns hex` now accepts "punctuation shorthand" patterns without commas surrounding them. For example, `{ mind } flock disint, hermes` is now parsed correctly.
- `/decode` now renders Introspection/Retrospection as `{`/`}` respectively and indents patterns between them.

### Fixed

- Fixed an incorrect lang key being used in `/mod`.
- Fixed `/decode` failing to parse hexes containing bubbles/motes/properties.
- Fixed incorrect pretty-printing of bubble iotas.

### Mods Added

- Hex-Ars Linker: 0.9.2.4

### Mods Updated

- HexDebug: 0.7.0+1.20.1
- HexFlow: 0.3.1.1
- HexParse: 1.4.0
- Hierophantics: 1.3.3
- Lapisworks: 1.5.5
- MoreIotas: 0.1.1

## `2.0.1` - 2025-10-02

### Fixed

- Fixed an issue where trailing zeros were stripped from integers in the title of `/patterns number` and Numerical Reflection.

## `2.0.0` - 2025-09-30

Initial release of HexBug v2, a total rewrite of the entire bot from the ground up.

### Added

- New commands:
  - `/book category`
  - `/book entry`
  - `/book recipe`
  - `/mods`
  - `/per-world-pattern`
- Added support for many more special handler patterns (eg. Sekhmet's Gambit).
- Added support for the new pattern overloading feature in Hex Casting 0.11.2, where the same pattern can do different things based on the values on the stack.
- Added proper localization support for all commands.
- Added zh-CN localization, by ChuijkYahus in [#36](https://github.com/object-Object/HexBug/pull/36) and [#37](https://github.com/object-Object/HexBug/pull/37).
- Started keeping a changelog and giving version numbers to releases.

### Changed

- Updated to Hex Casting 0.11.2 and Minecraft 1.20.1!
- Renamed commands:
  - `/patterns smart_number` -> `/patterns number`
  - `/decode upload` -> `/decode file`
- `/pattern check` now renders the checked pattern.
- Moved pattern rendering options from command arguments to a component-based menu.
- Styled text in pattern descriptions (links, bold, italic, etc) is now properly rendered using Markdown.
- Added the pattern ID to the pattern embed footer.
- Message names in `/info` are now properly localized.

### Removed

- Removed support for mods that don't have a hexdoc book.
- Removed `/source`, since hexdoc does not export the data required for this command to work.
- Removed `/pattern special bookkeepers_gambit` and `/pattern special numerical_reflection`; all special handlers are now directly in `/pattern special`.
- Removed a few outdated messages from `/info`.
