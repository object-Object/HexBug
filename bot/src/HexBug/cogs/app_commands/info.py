from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from discord import Embed, Interaction, app_commands
from discord.app_commands import Transform
from sqlalchemy.dialects.postgresql import insert

from HexBug.core.cog import HexBugCog
from HexBug.db.models import InfoMessage as InfoMessageRow
from HexBug.utils.discord.embeds import FOOTER_SEPARATOR
from HexBug.utils.discord.translation import (
    LocaleEnumTransformer,
    translate_choice_text,
    translate_command_text,
)
from HexBug.utils.discord.visibility import (
    Visibility,
    VisibilityOption,
    respond_with_visibility,
)
from HexBug.utils.strings import join_truthy


@dataclass(kw_only=True, eq=False)
class InfoMessageEmbed:
    title: bool = False
    description: bool = False
    url: str | None = None
    thumbnail: str | None = None
    image: str | None = None
    tracked: bool = False


class InfoMessage(Enum):
    addons = "https://addons.hexxy.media"

    bosnia = InfoMessageEmbed(
        description=True,
        thumbnail="https://media.hexxy.media/images/bosnia.png",
        tracked=True,
    )

    bug_report = InfoMessageEmbed(
        description=True,
    )

    crashlog = InfoMessageEmbed(
        description=True,
        image="https://hexxy.media/hexxy_media/i_will_not_give_crashlog.jpg",
    )

    forum = InfoMessageEmbed(
        title=True,
        description=True,
        url="https://forum.petra-k.at/index.php",
    )

    great_spells = "https://media.hexxy.media/data/great_spells.zip"

    gtp_itemdrop = InfoMessageEmbed(
        description=True,
    )

    patterns = "https://media.hexxy.media/data/patterns.csv"

    pluralkit = InfoMessageEmbed(
        description=True,
        thumbnail="https://hexxy.media/hexxy_media/why_is_the_bot_talking.png",
        tracked=True,
    )

    tools = "https://addons.hexxy.media/#tools"


class InfoCog(HexBugCog):
    @app_commands.command()
    async def info(
        self,
        interaction: Interaction,
        message: Transform[InfoMessage, LocaleEnumTransformer(InfoMessage)],
        visibility: VisibilityOption = Visibility.PRIVATE,
    ):
        value = message.value
        if isinstance(value, str):
            await respond_with_visibility(interaction, visibility, content=value)
            return

        embed = (
            Embed(
                title=await translate_choice_text(interaction, message, "title")
                if value.title
                else None,
                description=await translate_choice_text(
                    interaction, message, "description"
                )
                if value.description
                else None,
            )
            .set_thumbnail(url=value.thumbnail)
            .set_image(url=value.image)
        )

        if value.tracked:
            async with self.bot.db_session() as session:
                async with session.begin():
                    now = datetime.now()

                    if row := await session.get(InfoMessageRow, message.name):
                        days = (now - row.last_used).days
                    else:
                        days = None

                    stmt = (
                        insert(InfoMessageRow)
                        .values(
                            name=message.name,
                            usage_count=1,
                            last_used=now,
                        )
                        .on_conflict_do_update(
                            index_elements=[InfoMessageRow.name],
                            set_=dict(
                                usage_count=InfoMessageRow.usage_count + 1,
                                last_used=now,
                            ),
                        )
                        .returning(InfoMessageRow)
                    )
                    row = (await session.scalars(stmt)).one()

                embed.set_footer(
                    text=join_truthy(
                        FOOTER_SEPARATOR,
                        await translate_command_text(
                            interaction,
                            "footer-usage-count",
                            count=await row.awaitable_attrs.usage_count,
                        ),
                        await translate_command_text(
                            interaction, "footer-days-since", days=days
                        )
                        if days is not None
                        else None,
                    )
                )

        await respond_with_visibility(interaction, visibility, embed=embed)
