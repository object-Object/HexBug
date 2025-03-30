from __future__ import annotations

import logging
from datetime import datetime
from typing import Literal, Self

from pydantic import SecretStr
from pydantic_settings import BaseSettings as PydanticBaseSettings, SettingsConfigDict

from HexBug.utils.git import shorten_sha

logger = logging.getLogger(__name__)


SETTINGS_CONFIG = SettingsConfigDict(
    hide_input_in_errors=True,
    env_file=".env",
    extra="ignore",
)


class BaseSettings(PydanticBaseSettings):
    model_config = SETTINGS_CONFIG


class HexBugEnv(BaseSettings):
    environment: Literal["dev", "beta", "prod"]
    token: SecretStr

    api_port: int
    api_root_path: str

    deployment: DeploymentSettings | None = None

    @classmethod
    def load(cls) -> Self:
        return cls.model_validate({})


class DeploymentSettings(BaseSettings, env_prefix="deployment__"):
    timestamp: datetime

    commit_sha: str
    commit_timestamp: datetime
    commit_message: str

    @property
    def short_commit_sha(self):
        return shorten_sha(self.commit_sha)
