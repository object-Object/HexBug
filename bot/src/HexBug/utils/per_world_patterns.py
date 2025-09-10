from discord import Interaction
from hexdoc.core import ResourceLocation
from psycopg.errors import UniqueViolation
from sqlalchemy.exc import IntegrityError

from HexBug.core.bot import HexBugBot
from HexBug.core.exceptions import InvalidInputError
from HexBug.data.hex_math import HexPattern
from HexBug.data.patterns import PatternInfo
from HexBug.db.models import PerWorldPattern
from HexBug.ui.views.patterns import PerWorldPatternView
from HexBug.utils.discord.translation import translate
from HexBug.utils.discord.visibility import Visibility


async def add_per_world_pattern(
    interaction: Interaction,
    pattern: HexPattern,
    pattern_id: ResourceLocation,
    info: PatternInfo | None,
):
    assert interaction.guild_id
    bot = HexBugBot.of(interaction)

    # insert the pattern
    try:
        async with bot.db_session() as session, session.begin():
            session.add(
                PerWorldPattern(
                    id=pattern_id,
                    guild_id=interaction.guild_id,
                    user_id=interaction.user.id,
                    direction=pattern.direction,
                    signature=pattern.signature,
                )
            )
    except IntegrityError as e:
        if isinstance(e.orig, UniqueViolation):
            raise InvalidInputError(
                "Pattern has already been added to this server's database.",
                value=pattern.display(),
            ).add_field(
                name="Pattern",
                value=info.name if info else str(pattern_id),
            )
        raise

    await PerWorldPatternView(
        interaction=interaction,
        pattern=pattern,
        pattern_id=pattern_id,
        info=info,
        contributor=interaction.user,
        add_visibility_buttons=False,
    ).send(
        interaction,
        Visibility.PRIVATE,
        content=await translate(interaction, "per-world-pattern-added"),
    )
