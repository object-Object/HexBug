# HexBug-data

Standalone registry code and parsers for [HexBug](https://github.com/object-Object/HexBug), a Discord bot for Hex Casting.

This is published to PyPI for use in projects which would like to use HexBug's registry as a data source.

## Getting the data

### Pre-built dumps

Registry dumps are uploaded to the [Book of Hexxy](https://book.hexxy.media) for each release (eg. https://book.hexxy.media/v/2.4.0/registry.json). The `registry.json` file can be imported using `HexBugRegistry.load()`.

### Building

If you'd rather build the registry yourself, you'll need to install HexBug-data with the `full` extra. Since many addons are not currently published to PyPI, constraint files are uploaded to the [Book of Hexxy](https://book.hexxy.media) for each release:
- https://book.hexxy.media/v/2.4.0/dist/constraints.txt
- https://book.hexxy.media/v/2.4.0/dist/pylock.toml

For example:

```sh
uv pip install HexBug-data[full] --constraints constraints.txt
```

Depending on the version, you may also need to install some packages from HexBug's [vendor](https://github.com/object-Object/HexBug/tree/main/vendor) directory.
