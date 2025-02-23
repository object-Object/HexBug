import logging

import discord


def setup_logging(verbose: bool = False):
    discord.utils.setup_logging()
    logging.getLogger("HexBug").setLevel(logging.DEBUG)
    if not verbose:
        logging.getLogger("httpx").setLevel(logging.WARNING)
    discord.VoiceClient.warn_nacl = False
