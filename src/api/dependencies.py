from __future__ import annotations

from typing import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.domain.api_token import ApiToken
from src.ports.token_signer import TokenSigner

_BEARER_SCHEME = HTTPBearer()

_ERR_INVALID_TOKEN: str = "Invalid or expired token"
_ERR_AUTH_HEADER: str = "WWW-Authenticate"
_ERR_AUTH_VALUE: str = "Bearer"


def make_token_verifier(
    signer: TokenSigner,
) -> Callable[[HTTPAuthorizationCredentials], ApiToken]:
    def verify_token(
        credentials: HTTPAuthorizationCredentials = Depends(_BEARER_SCHEME),
    ) -> ApiToken:
        try:
            return signer.verify(credentials.credentials)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=_ERR_INVALID_TOKEN,
                headers={_ERR_AUTH_HEADER: _ERR_AUTH_VALUE},
            )

    return verify_token
