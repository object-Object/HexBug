from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Sequence

import jwt
from jwt import PyJWK
from pydantic import BaseModel

if TYPE_CHECKING:
    from jwt.algorithms import AllowedPrivateKeys, AllowedPublicKeys


class JWTModel(BaseModel):
    @classmethod
    def decode_jwt(
        cls,
        token: str | bytes,
        *,
        key: AllowedPublicKeys | PyJWK | str | bytes = "",
        algorithms: Sequence[str] | None = None,
    ):
        return cls.model_validate(jwt.decode(jwt=token, key=key, algorithms=algorithms))

    def encode_jwt(
        self,
        *,
        key: AllowedPrivateKeys | PyJWK | str | bytes,
        algorithm: str | None = None,
        expires: datetime | None = None,
    ) -> str:
        payload = self.model_dump(mode="json")
        if expires:
            payload["exp"] = expires
        return jwt.encode(
            payload=payload,
            key=key,
            algorithm=algorithm,
        )
