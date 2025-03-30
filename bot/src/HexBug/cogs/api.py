from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Annotated

from fastapi import Depends, FastAPI, Response
from pydantic import BaseModel
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR
from uvicorn import Config, Server

from HexBug.core.bot import HexBugBot
from HexBug.core.cog import HexBugCog

logger = logging.getLogger(__name__)


class HealthInfo(BaseModel):
    websocket_latency: float


app = FastAPI()


def get_bot():
    bot = app.state.bot
    assert isinstance(bot, HexBugBot), f"Invalid state.bot, expected HexBugBot: {bot}"
    return bot


BotDependency = Annotated[HexBugBot, Depends(get_bot)]


@app.get("/health")
async def get_health(
    bot: BotDependency,
    response: Response,
) -> HealthInfo:
    if bot.latency > 180:  # seconds
        logger.error(f"WebSocket latency too high: {bot.latency:.2f}")
        response.status_code = HTTP_500_INTERNAL_SERVER_ERROR

    return HealthInfo(
        websocket_latency=bot.latency,
    )


@dataclass(eq=False)
class APICog(HexBugCog):
    server: Server | None = field(default=None, init=False)

    async def cog_load(self):
        await super().cog_load()
        app.state.bot = self.bot
        self.server = Server(
            Config(
                app,
                host="0.0.0.0",
                port=self.env.api_port,
                root_path=self.env.api_root_path,
            )
        )
        self.bot.loop.create_task(self.server.serve())

    async def cog_unload(self):
        if self.server:
            await self.server.shutdown()
            self.server = None
