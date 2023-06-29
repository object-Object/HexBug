from typing import TypedDict

from aiohttp import ClientSession

MODRINTH_ROOT = "https://api.modrinth.com/v2/"
USER_AGENT = "object-Object/HexBug (object@objectobject.ca)"


class Version(TypedDict):
    name: str
    version_number: str
    version_type: str
    status: str
    date_published: str


async def _get_endpoint(session: ClientSession, endpoint: str):
    async with session.get(
        MODRINTH_ROOT + endpoint,
        headers={"User-Agent": USER_AGENT},
    ) as resp:
        resp.raise_for_status()
        return await resp.json()


async def get_versions(session: ClientSession, slug: str) -> list[Version]:
    return await _get_endpoint(session, f"project/{slug}/version")
