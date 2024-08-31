# Contributing to HexBug

WIP.

## General guidelines

* If at all possible, use VSCode and install the recommended extensions. This has two major benefits:
  * You'll (hopefully) see the same IDE warnings/errors as I would.
  * Format on Save will ensure that the project's code style stays consistent.
* Set up your environment as explained in [README.md](./README.md), **including creating a venv**. Make sure you're using the required Python version. This ensures that you're using exactly and only the same packages and versions as I am.
* In general, please actually run and test the code you're contributing, and make sure there are no errors at runtime or from the type checker.

## Adding a mod

* Fork, clone, and set up the bot as explained in [README.md](./README.md).
* If your web book uses the old `collate_data.py` system, add your mod's repository as a submodule here.
* If your web book uses hexdoc:
  * If you enabled PyPI publishing for your hexdoc plugin (recommended), add a pinned dependency to the `pyproject.toml` file in `project.dependencies`.
    * Example: `hexdoc-oneironaut==0.1.2.1.0`
  * Otherwise, you can do **either** of the following options:
    * Add a direct dependency to a permalinked wheel for your plugin to `pyproject.toml`.
      * Example: `hexdoc-hexgloop @ https://github.com/SamsTheNerd/HexGloop/raw/af72e6cc318d/docs/v/latest/main/dist/hexdoc_hexgloop-0.2.1.1.0.dev0-py3-none-any.whl`
    * Add a wheel for your plugin to `vendor/`, then add a pinned dependency to `pyproject.toml`. You can get the wheel from your GitHub Actions web book workflow in the `hexdoc-build` artifact.
      * Example: `hexdoc-hexal==0.2.19.1.0.dev0`
* Add your mod to `src/HexBug/utils/mods.py` in the `RegistryMod`, `APIMod`, or `HexdocMod` enum, depending which system your web book is based on. Use the existing mods as examples. If necessary, add a subclass for your mod.
* Run the book type scraper command listed in [README.md](./README.md).
* Test it out:
  * Try running the bot. You'll need to [create a bot account](https://discordpy.readthedocs.io/en/stable/discord.html) and put the token in `.env` as explained in [README.md](./README.md).
  * Make sure HexBug actually starts without any errors or warnings. Note that the warning about `HexCasting:sentinel/create/great` missing a URL is normal.
  * Run the chat command `@YourBotAccount sync` to sync slash commands to your current server, then try running some commands. Ensure everything works and there are no console errors. For example:
    * `/mod YourModName`
    * `/pattern name APatternInYourMod`
    * `/book home YourMod`
    * `/book page YourMod APageInYourMod`
    * `/source repo YourMod`
    * `/source pattern APatternInYourMod`
* After ensuring there are no runtime or type errors, submit a PR.

## Tips

* If you see a bunch of nonsensical errors from Pylance showing up, try adding and deleting some text to one of the Python files. That should trigger it to refresh and the errors should disappear. I'm not sure what causes this.
