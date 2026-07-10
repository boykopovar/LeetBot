from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from src.api.dependencies import make_token_verifier
from src.api.routes.mail import make_mail_router
from src.infrastructure.in_memory_mailbox import InMemoryMailbox
from src.infrastructure.in_memory_session_store import InMemorySessionStore
from src.ports.token_signer import TokenSigner

_API_TITLE: str = "LeetBot API"
_API_VERSION: str = "1.0.0"
_API_DESCRIPTION: str = (
    "Disposable email inbox via Telegram bot.\n\n"
    "Authenticate with a Bearer JWT token obtained via the `/apikey` command in Telegram.\n\n"
    "```\nAuthorization: Bearer <token>\n```"
)
_SECURITY_SCHEME_NAME: str = "BearerAuth"
_SECURITY_SCHEME: dict = {
    _SECURITY_SCHEME_NAME: {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
        "description": "JWT token obtained via /apikey command in Telegram.",
    }
}
_ALLOWED_METHODS: list[str] = ["GET", "POST", "DELETE", "OPTIONS"]
_ALLOWED_HEADERS: list[str] = ["Authorization", "Content-Type"]


def create_app(store: InMemorySessionStore, signer: TokenSigner, mailbox: InMemoryMailbox) -> FastAPI:
    app = FastAPI(title=_API_TITLE, version=_API_VERSION, description=_API_DESCRIPTION)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=_ALLOWED_METHODS,
        allow_headers=_ALLOWED_HEADERS,
    )
    token_dependency = make_token_verifier(signer)
    app.include_router(make_mail_router(store, mailbox, token_dependency))

    def custom_openapi() -> dict:
        if app.openapi_schema:
            return app.openapi_schema
        schema = get_openapi(
            title=_API_TITLE,
            version=_API_VERSION,
            description=_API_DESCRIPTION,
            routes=app.routes,
        )
        schema.setdefault("components", {})["securitySchemes"] = _SECURITY_SCHEME
        for path in schema.get("paths", {}).values():
            for operation in path.values():
                operation["security"] = [{_SECURITY_SCHEME_NAME: []}]
        app.openapi_schema = schema
        return schema

    app.openapi = custom_openapi  # type: ignore[method-assign]
    return app
