from fastapi import FastAPI

from src.api.dependencies import make_token_verifier
from src.api.routes.mail import make_mail_router
from src.infrastructure.in_memory_mailbox import InMemoryMailbox
from src.infrastructure.in_memory_session_store import InMemorySessionStore
from src.ports.token_signer import TokenSigner

_API_TITLE: str = "LeetBot API"
_API_VERSION: str = "1.0.0"


def create_app(store: InMemorySessionStore, signer: TokenSigner, mailbox: InMemoryMailbox) -> FastAPI:
    app = FastAPI(title=_API_TITLE, version=_API_VERSION)
    token_dependency = make_token_verifier(signer)
    app.include_router(make_mail_router(store, mailbox, token_dependency))
    return app
