from __future__ import annotations

from dataclasses import dataclass, field
from typing import Generic, Literal, LiteralString, TypedDict, TypeVar

from aiohttp import ClientSession

from utils.book_types import BookCategory

T = TypeVar("T", bound=LiteralString)


class APIVersion(TypedDict):
    id: str
    path: str
    published: str
    """ISO 8601"""


class APIVersions(TypedDict):
    latest: str
    latestPublished: str
    """ISO 8601"""
    versions: list[APIVersion]
    """Sorted by descending release date"""


class APIDocsBook(TypedDict):
    webPath: str
    dumpPath: str


class APIDocs(TypedDict):
    availableLangFiles: list[str]
    defaultLangFile: str
    patternPath: str
    book: APIDocsBook
    repositoryRoot: str
    commitHash: str


class _BaseAPIPatternSource(TypedDict, Generic[T]):
    type: T
    path: str


class APILocalPatternSource(_BaseAPIPatternSource[Literal["local"]]):
    pass


class APIExternalPatternSource(_BaseAPIPatternSource[Literal["external"]]):
    jar: str


APIPatternSource = APILocalPatternSource | APIExternalPatternSource


class APIPattern(TypedDict):
    id: str
    defaultStartDir: str
    angleSignature: str
    className: str
    isPerWorld: bool
    source: APIPatternSource


@dataclass
class API:
    root_url: str

    async def _get_endpoint(self, session: ClientSession, endpoint: str):
        async with session.get(self.root_url + endpoint) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def get_docs(self, session: ClientSession) -> APIDocs:
        return await self._get_endpoint(session, "docs.json")

    async def get_lang(self, session: ClientSession, docs: APIDocs) -> dict[str, str]:
        return await self._get_endpoint(session, docs["defaultLangFile"])

    async def get_patterns(self, session: ClientSession, docs: APIDocs) -> list[APIPattern]:
        return await self._get_endpoint(session, docs["patternPath"])

    async def get_book(self, session: ClientSession, docs: APIDocs) -> list[BookCategory]:
        return await self._get_endpoint(session, docs["book"]["dumpPath"])

    def get_book_url(self, docs: APIDocs) -> str:
        return self.root_url + docs["book"]["webPath"]
