import logging

import discord


def setup_logging(verbose: bool = False):
    discord.utils.setup_logging()
    logging.getLogger("HexBug").setLevel(logging.DEBUG)
    if verbose:
        logging.getLogger("hexdoc").setLevel(logging.DEBUG)
    else:
        logging.getLogger("hexdoc").setLevel(logging.INFO)
        logging.getLogger("hexdoc.minecraft.assets.textures").setLevel(logging.ERROR)
        logging.getLogger("httpx").setLevel(logging.WARNING)
    discord.VoiceClient.warn_nacl = False
