from __future__ import annotations

import logging
import math
import sys
from asyncio import Task
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Annotated, Any, cast, overload

import discordoauth2
from fastapi import Depends, FastAPI, HTTPException, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from httpx import AsyncClient
from jwt import InvalidTokenError
from pydantic import BaseModel, ValidationError
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_500_INTERNAL_SERVER_ERROR
from uvicorn import Config, Server

from HexBug.cogs.app_commands.patterns import PatternsCog
from HexBug.core.bot import HexBugBot
from HexBug.core.cog import HexBugCog
from HexBug.data.hex_math import HexPattern
from HexBug.utils.jwt import JWTModel

logger = logging.getLogger(__name__)


class HealthInfo(BaseModel):
    websocket_latency: float
    longest_active_command_runtime: float | None


# Keep in sync with activity/src/hooks/useDiscordAuth.ts
class ActivityTokenRequest(BaseModel):
    code: str


# Keep in sync with activity/src/hooks/useDiscordAuth.ts
class ActivityTokenResponse(BaseModel):
    access_token: str
    api_token: str


# Keep in sync with activity/src/hooks/useDiscordAuth.ts
class ActivityAPIToken(JWTModel):
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


def get_activity_api_token(
    token: Annotated[HTTPAuthorizationCredentials, Depends(HTTPBearer())],
    bot: BotDependency,
) -> ActivityAPIToken:
    try:
        return ActivityAPIToken.decode_jwt(
            token.credentials,
            key=bot.env.jwt_public_key,
            algorithms=["EdDSA"],
        )
    except (InvalidTokenError, ValidationError):
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


ActivityAPITokenDependency = Annotated[
    ActivityAPIToken, Depends(get_activity_api_token)
]


@app.get("/health")
async def get_health(
    bot: BotDependency,
    response: Response,
) -> HealthInfo:
    if bot.latency > 30:  # seconds
        logger.error(f"WebSocket latency too high: {bot.latency:.2f} s")
        response.status_code = HTTP_500_INTERNAL_SERVER_ERROR

    longest_active_command_runtime = bot.get_longest_active_command_runtime()
    if (
        longest_active_command_runtime is not None
        and longest_active_command_runtime > 10
    ):
        logger.error(
            f"A command has been running for too long: {longest_active_command_runtime:.2f} s"
        )
        response.status_code = HTTP_500_INTERNAL_SERVER_ERROR

    return HealthInfo(
        websocket_latency=to_finite(bot.latency),
        longest_active_command_runtime=to_finite(longest_active_command_runtime),
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

    api_token = ActivityAPIToken(
        user_id=identify["id"],
    ).encode_jwt(
        key=bot.env.jwt_private_key.get_secret_value(),
        algorithm="EdDSA",
        expires=datetime.now(timezone.utc) + timedelta(minutes=30),
    )

    return ActivityTokenResponse(
        access_token=access.token,
        api_token=api_token,
    )


@app.post("/activity/patterns")
async def post_activity_patterns(
    body: list[HexPattern],
    bot: BotDependency,
    api_token: ActivityAPITokenDependency,
):
    patterns_cog = cast(PatternsCog, bot.get_cog("Patterns"))

    if value := patterns_cog.draw_messages.get(int(api_token.user_id)):
        value.view.patterns = body
        value.view.embed.description = None if body else value.empty_text
        try:
            await value.view.refresh(value.interaction, value.message)
        except Exception:
            logger.warning("Failed to refresh activity patterns view", exc_info=True)
            value.view.on_stop_drawing()


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


@overload
def to_finite(value: float) -> float: ...
@overload
def to_finite(value: float | None) -> float | None: ...
def to_finite(value: float | None) -> float | None:
    if value is None:
        return None
    if math.isfinite(value):
        return value
    return sys.float_info.max
