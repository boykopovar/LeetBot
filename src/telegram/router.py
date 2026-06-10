from aiogram import Dispatcher

from src.infrastructure.in_memory_session_store import InMemorySessionStore
from src.ports.token_signer import TokenSigner
from src.telegram.handlers.apikey_command import make_apikey_router
from src.telegram.handlers.email_command import make_email_router
from src.telegram.handlers.random_command import make_random_router
from src.telegram.handlers.stop_command import make_stop_router
from src.telegram.middleware import UpdateLogMiddleware


def register_all_routers(
    dp: Dispatcher,
    store: InMemorySessionStore,
    signer: TokenSigner,
    ttl_days: int,
    docs_url: str,
) -> None:
    dp.update.outer_middleware(UpdateLogMiddleware())
    dp.include_router(make_email_router(store))
    dp.include_router(make_random_router(store))
    dp.include_router(make_stop_router(store))
    dp.include_router(make_apikey_router(signer, ttl_days, docs_url))
