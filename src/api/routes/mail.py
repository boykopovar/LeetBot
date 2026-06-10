from typing import Callable, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr

from src.domain.api_token import ApiToken
from src.env_tools import ADMIN_IDS, DOMAIN, RANDOM_KEY, SESSION_TTL_SECONDS
from src.infrastructure.in_memory_mailbox import InMemoryMailbox
from src.infrastructure.in_memory_session_store import InMemorySessionStore
from src.services.random_email_service import belongs_to_user, generate_local, random_nonce
from src.services.session_service import get_active_email, register_session

_AT: str = "@"
_ERR_NO_SESSION: str = "No active session"
_ERR_WRONG_DOMAIN: str = "Email must use domain: {domain}"
_ERR_NOT_YOURS: str = "This address does not belong to your account"
_ERR_OVERFLOW: str = "Address generation is not available for your account ID"
_MINUTES: int = SESSION_TTL_SECONDS // 60
_ROUTE_SESSION: str = "/session"
_ROUTE_SESSION_RANDOM: str = "/session/random"
_ROUTE_MAIL_POLL: str = "/mail/poll"
_ROUTER_PREFIX: str = "/mail"
_ROUTER_TAG: str = "mail"
_POLL_TIMEOUT_SECONDS: float = 30.0


class _SessionResponse(BaseModel):
    email: str
    expires_in_minutes: int


class _RegisterRequest(BaseModel):
    email: EmailStr


class _MailMessageResponse(BaseModel):
    sender: str
    subject: str
    body_html: str
    received_at_unix: int
    sender_ip: str
    originating_ip: Optional[str]


def make_mail_router(
    store: InMemorySessionStore,
    mailbox: InMemoryMailbox,
    token_dependency: Callable[[], ApiToken],
) -> APIRouter:
    router = APIRouter(prefix=_ROUTER_PREFIX, tags=[_ROUTER_TAG])

    @router.get(_ROUTE_SESSION, response_model=_SessionResponse)
    async def get_session(token: ApiToken = Depends(token_dependency)) -> _SessionResponse:
        email: Optional[str] = get_active_email(store, token.user_id)
        if email is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_ERR_NO_SESSION)
        return _SessionResponse(email=email, expires_in_minutes=_MINUTES)

    @router.post(_ROUTE_SESSION, response_model=_SessionResponse, status_code=status.HTTP_201_CREATED)
    async def register(
        body: _RegisterRequest,
        token: ApiToken = Depends(token_dependency),
    ) -> _SessionResponse:
        normalized: str = str(body.email).lower()
        domain_part = normalized.split(_AT)[-1]
        if domain_part != DOMAIN:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=_ERR_WRONG_DOMAIN.format(domain=DOMAIN),
            )
        local = normalized.split(_AT)[0]
        if token.user_id not in ADMIN_IDS:
            if not belongs_to_user(RANDOM_KEY, token.user_id, local):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=_ERR_NOT_YOURS,
                )
        await register_session(store, token.user_id, normalized, SESSION_TTL_SECONDS)
        return _SessionResponse(email=normalized, expires_in_minutes=_MINUTES)

    @router.post(_ROUTE_SESSION_RANDOM, response_model=_SessionResponse, status_code=status.HTTP_201_CREATED)
    async def register_random(token: ApiToken = Depends(token_dependency)) -> _SessionResponse:
        try:
            local = generate_local(RANDOM_KEY, token.user_id, random_nonce())
        except OverflowError:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=_ERR_OVERFLOW)
        email = local + _AT + DOMAIN
        await register_session(store, token.user_id, email, SESSION_TTL_SECONDS)
        return _SessionResponse(email=email, expires_in_minutes=_MINUTES)

    @router.get(_ROUTE_MAIL_POLL, response_model=Optional[_MailMessageResponse])
    async def poll_mail(token: ApiToken = Depends(token_dependency)) -> Optional[_MailMessageResponse]:
        deadline: Optional[float] = store.get_deadline(token.user_id)
        if deadline is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_ERR_NO_SESSION)
        message = await mailbox.poll(token.user_id, deadline, _POLL_TIMEOUT_SECONDS)
        if message is None:
            return None
        return _MailMessageResponse(
            sender=message.sender,
            subject=message.subject,
            body_html=message.body_html,
            received_at_unix=message.received_at_unix,
            sender_ip=message.sender_ip,
            originating_ip=message.originating_ip,
        )

    return router
