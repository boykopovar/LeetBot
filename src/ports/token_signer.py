from typing_extensions import Protocol

from src.domain.api_token import ApiToken


class TokenSigner(Protocol):
    def sign(self, user_id: int) -> str: ...
    def verify(self, token: str) -> ApiToken: ...
