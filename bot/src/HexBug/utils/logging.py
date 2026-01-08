import logging

import discord
import lark.utils

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False):
    if verbose:
        levels = {
            None: logging.DEBUG,
            "lark": logging.DEBUG,
        }
    else:
        levels = {
            None: logging.INFO,
            "HexBug": logging.DEBUG,
            "hexdoc.minecraft.assets.textures": logging.ERROR,
            "httpx": logging.WARNING,
            "prometheus": logging.DEBUG,
        }

    # :/
    for handler in lark.utils.logger.handlers:
        lark.utils.logger.removeHandler(handler)

    discord.utils.setup_logging()
    discord.VoiceClient.warn_nacl = False
    for name, level in levels.items():
        logging.getLogger(name).setLevel(level)

    logger.debug("Logger initialized.")
