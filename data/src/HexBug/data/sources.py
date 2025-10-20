from abc import ABC, abstractmethod
from typing import Annotated, Literal, override

from pydantic import BaseModel, Field, RootModel
from yarl import URL


class BaseUserInfo(BaseModel, ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def url(self) -> URL: ...

    @property
    def icon_url(self) -> URL:
        return self.url.with_suffix(".png")


class BaseSourceInfo[T: BaseUserInfo](BaseModel, ABC):
    author: T
    repo: str
    commit: str

    @property
    @abstractmethod
    def url(self) -> URL: ...

    @property
    @abstractmethod
    def permalink(self) -> URL: ...

    @property
    @abstractmethod
    def asset_url(self) -> URL: ...

    @property
    def search_term(self) -> str:
        return f"{self.author.name}/{self.repo}"


class GitHubUserInfo(BaseUserInfo, RootModel[str]):
    @property
    @override
    def name(self) -> str:
        return self.root

    @property
    @override
    def url(self) -> URL:
        return URL("https://github.com") / self.name


class GitHubSourceInfo(BaseSourceInfo[GitHubUserInfo]):
    type: Literal["github"] = "github"

    @property
    @override
    def url(self) -> URL:
        return self.author.url / self.repo

    @property
    @override
    def permalink(self) -> URL:
        return self.url / "tree" / self.commit

    @property
    @override
    def asset_url(self) -> URL:
        return (
            URL("https://raw.githubusercontent.com")
            / self.author.name
            / self.repo
            / self.commit
        )


class CodebergUserInfo(BaseUserInfo, RootModel[str]):
    @property
    @override
    def name(self) -> str:
        return self.root

    @property
    @override
    def url(self) -> URL:
        return URL("https://codeberg.org") / self.name


class CodebergSourceInfo(BaseSourceInfo[CodebergUserInfo]):
    type: Literal["codeberg"] = "codeberg"

    @property
    @override
    def url(self) -> URL:
        return self.author.url / self.repo

    @property
    @override
    def permalink(self) -> URL:
        return self.url / "src/commit" / self.commit

    @property
    @override
    def asset_url(self) -> URL:
        return self.url / "raw/commit" / self.commit


type UserInfo = GitHubUserInfo | CodebergUserInfo


type SourceInfo = Annotated[
    GitHubSourceInfo | CodebergSourceInfo,
    Field(discriminator="type"),
]
