# Contributing to HexBug

This document is a work-in-progress.

## General guidelines

* If at all possible, use VSCode and install the recommended extensions. This has two major benefits:
  * You'll (hopefully) see the same IDE warnings/errors as I would.
  * Format on Save will ensure that the project's code style stays consistent.
* Set up your environment as explained in `README.md`, **including creating a venv**. Make sure you're using the required Python version. This ensures that you're using exactly and only the same packages and versions as I am.
* In general, please actually run and test the code you're contributing, and make sure there are no errors at runtime or from the type checker.

## Adding a mod

* If your mod doesn't provide something like [Hexbound's docs API](https://hexbound.cypher.coffee/latest/docs.json), add your mod's repository as a submodule here.
* Add your mod to `utils/mods.py` in either the `RegistryMod` or `APIMod` enum, depending if your mod provides a docs API. Use the existing mods as examples. If necessary, add a subclass for your mod.
* Run the book type scraper command listed in the README.
* Test it out:
  * Try running the bot. You'll need to [create a bot account](https://discordpy.readthedocs.io/en/stable/discord.html) and put the token in `.env` as explained in the README.
  * Make sure HexBug actually starts without any errors or warnings. Note that the warning about `HexCasting:sentinel/create/great` missing a URL is normal.
  * Run the chat command `@YourBotAccount sync` to sync slash commands to your current server, then try running some commands. Ensure everything works and there are no console errors. For example:
    * `/mod YourModName`
    * `/info addons`
    * `/pattern name APatternInYourMod`
    * `/book home YourMod`
    * `/book page YourMod APageInYourMod`
    * `/source repo YourMod`
    * `/source pattern APatternInYourMod`
* After ensuring there are no runtime or type errors, submit a PR.

## Tips

* If you see a bunch of nonsensical errors from Pylance showing up, try adding and deleting some text to one of the Python files. That should trigger it to refresh and the errors should disappear. I'm not sure what causes this.
