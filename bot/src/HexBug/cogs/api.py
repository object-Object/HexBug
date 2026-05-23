from __future__ import annotations

import logging
import math
import sys
from asyncio import Task
from dataclasses import dataclass, field
from typing import Annotated, Any, cast

import discordoauth2
import jwt
from fastapi import Depends, FastAPI, Response
from httpx import AsyncClient
from pydantic import BaseModel
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR
from uvicorn import Config, Server

from HexBug.core.bot import HexBugBot
from HexBug.core.cog import HexBugCog

logger = logging.getLogger(__name__)


class HealthInfo(BaseModel):
    websocket_latency: float


# Keep in sync with activity/src/hooks/useDiscordAuth.ts
class ActivityTokenRequest(BaseModel):
    code: str


# Keep in sync with activity/src/hooks/useDiscordAuth.ts
class ActivityTokenResponse(BaseModel):
    access_token: str
    api_token: str


# Keep in sync with activity/src/hooks/useDiscordAuth.ts
class ActivityAPIToken(BaseModel):
    user_id: str


app = FastAPI()


def get_dependency[T](value_type: type[T], name: str):
    def getter() -> T:
        value = getattr(app.state, name)
        assert isinstance(value, value_type), (
            f"Invalid state.{name}, expected {value_type.__name__}: {value}"
        )
        return value

    return Depends(getter)


BotDependency = Annotated[HexBugBot, get_dependency(HexBugBot, "bot")]
ClientDependency = Annotated[AsyncClient, get_dependency(AsyncClient, "client")]
OAuthClientDependency = Annotated[
    discordoauth2.AsyncClient, get_dependency(discordoauth2.AsyncClient, "oauth_client")
]


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


@app.post("/activity/token")
async def post_activity_token(
    body: ActivityTokenRequest,
    bot: BotDependency,
    oauth_client: OAuthClientDependency,
) -> ActivityTokenResponse:
    access = await oauth_client.exchange_code(body.code)
    identify = cast(
        dict[str, Any],
        await access.fetch_identify(),  # pyright: ignore[reportUnknownMemberType]
    )

    api_token = jwt.encode(
        payload=ActivityAPIToken(
            user_id=identify["id"],
        ).model_dump(mode="json"),
        key=bot.env.jwt_private_key.get_secret_value(),
        algorithm="EdDSA",
    )

    return ActivityTokenResponse(
        access_token=access.token,
        api_token=api_token,
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
        app.root_path = self.env.api_root_path
        app.state.bot = self.bot
        app.state.client = AsyncClient()
        app.state.oauth_client = discordoauth2.AsyncClient(
            id=self.env.client_id,
            secret=self.env.client_secret.get_secret_value(),
            redirect="",
        )
        self.server = Server(
            Config(
                app,
                host="0.0.0.0",
                port=self.env.api_port,
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
        if client := cast(AsyncClient | None, app.state.client):
            await client.aclose()
