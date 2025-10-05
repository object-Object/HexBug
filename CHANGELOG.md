# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and [Pydantic's HISTORY.md](https://github.com/pydantic/pydantic/blob/main/HISTORY.md), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [UNRELEASED]

### Changed

- Added more shorthand names to a few patterns in `/patterns hex`.
- `/patterns hex` now accepts "punctuation shorthand" patterns without commas surrounding them. For example, `{ mind } flock disint, hermes` is now parsed correctly.
- `/decode` now renders Introspection/Retrospection as `{`/`}` respectively and indents patterns between them.

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
