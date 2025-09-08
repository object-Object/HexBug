from __future__ import annotations

import logging
import math
import sys
from asyncio import Task
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
        websocket_latency=bot.latency
        if math.isfinite(bot.latency)
        else sys.float_info.max,
    )


@dataclass(eq=False)
class APICog(HexBugCog):
    server: Server | None = field(default=None, init=False)
    server_task: Task[None] | None = field(default=None, init=False)

    async def cog_load(self):
        await super().cog_load()
        if not self.bot.should_run:
            logger.info("Skipping API start because should_run is False")
            return
        app.state.bot = self.bot
        self.server = Server(
            Config(
                app,
                host="0.0.0.0",
                port=self.env.api_port,
                root_path=self.env.api_root_path,
            )
        )
        # use _serve to prevent the server from trying to capture signals
        self.server_task = self.bot.loop.create_task(self.server._serve())  # pyright: ignore[reportPrivateUsage]

    async def cog_unload(self):
        if server := self.server:
            self.server = None
            server.should_exit = True
        if task := self.server_task:
            self.server_task = None
            await task
