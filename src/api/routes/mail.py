from typing import Callable, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field

from src.domain.api_token import ApiToken
from src.env_tools import ADMIN_IDS, DOMAIN, RANDOM_KEY, SESSION_TTL_SECONDS
from src.infrastructure.in_memory_mailbox import InMemoryMailbox
from src.infrastructure.in_memory_session_store import InMemorySessionStore
from src.services.random_email_service import belongs_to_user, generate_local, random_nonce
from src.services.session_service import get_active_email, register_session, stop_session

_AT: str = "@"
_ERR_NO_SESSION: str = "No active session"
_ERR_WRONG_DOMAIN: str = "Email must use domain: {domain}"
_ERR_NOT_YOURS: str = "This address does not belong to your account"
_ERR_OVERFLOW: str = "Address generation is not available for your account ID"
_MINUTES: int = SESSION_TTL_SECONDS // 60
_ROUTE_SESSION: str = "/session"
_ROUTE_SESSION_RANDOM: str = f"{_ROUTE_SESSION}/random"
_ROUTER_PREFIX: str = "/mail"
_ROUTE_MAIL_POLL: str = f"{_ROUTER_PREFIX}/poll"
_ROUTER_TAG: str = "mail"
_POLL_TIMEOUT_SECONDS: float = 30.0

_DESC_GET_SESSION: str = (
    "Returns the currently active session for the authenticated user. "
    "A session is created via `POST /mail/session` or `POST /mail/session/random` "
    "and expires after the configured `SESSION_MINUTES`."
)
_DESC_POST_SESSION: str = (
    "Registers a session on a specific address belonging to the authenticated user. "
    "The address must use the server domain. "
    "Admins (configured via `ADMIN_IDS`) may register any address on the domain. "
    "Replaces any previously active session."
)
_DESC_POST_SESSION_RANDOM: str = (
    "Generates a random address from the user's deterministic address space "
    "and registers a session on it. "
    "Each call produces a different address. "
    "Replaces any previously active session."
)
_DESC_DELETE_SESSION: str = (
    "Stops the active session immediately. "
    "Equivalent to the `/stop` command in Telegram. "
    "After this call the address will no longer accept incoming mail."
)
_DESC_POLL: str = (
    "Long-polls for an incoming message on the active session. "
    "The connection is held open for up to 30 seconds. "
    "Returns the message as soon as it arrives, or `null` if the timeout elapses. "
    "Call repeatedly in a loop to continuously receive mail."
)

_DESC_FIELD_EMAIL_RESP: str = "Full email address of the active session."
_DESC_FIELD_EXPIRES: str = "Remaining session lifetime in minutes."
_DESC_FIELD_SENDER: str = "Envelope sender address."
_DESC_FIELD_SUBJECT: str = "Message subject line."
_DESC_FIELD_BODY_HTML: str = "HTML body of the message."
_DESC_FIELD_RECEIVED_AT: str = "Unix timestamp of when the message was received by the SMTP server."
_DESC_FIELD_SENDER_IP: str = "IP address of the connecting SMTP client."
_DESC_FIELD_ORIG_IP: str = (
    "Value of the `X-Originating-IP` header, if present in the message. "
    "Absent for most senders."
)
_DESC_FIELD_EMAIL_REQ: str = "Address to register. Must belong to the server domain and to your account."


class _SessionResponse(BaseModel):
    email: str = Field(description=_DESC_FIELD_EMAIL_RESP)
    expires_in_minutes: int = Field(description=_DESC_FIELD_EXPIRES)


class _MailMessageResponse(BaseModel):
    sender: str = Field(description=_DESC_FIELD_SENDER)
    subject: str = Field(description=_DESC_FIELD_SUBJECT)
    body_html: str = Field(description=_DESC_FIELD_BODY_HTML)
    received_at_unix: int = Field(description=_DESC_FIELD_RECEIVED_AT)
    sender_ip: str = Field(description=_DESC_FIELD_SENDER_IP)
    originating_ip: Optional[str] = Field(default=None, description=_DESC_FIELD_ORIG_IP)


def make_mail_router(
    store: InMemorySessionStore,
    mailbox: InMemoryMailbox,
    token_dependency: Callable[[], ApiToken],
) -> APIRouter:
    router = APIRouter(prefix=_ROUTER_PREFIX, tags=[_ROUTER_TAG])

    class _RegisterRequest(BaseModel):
        model_config = {"json_schema_extra": {"example": {"email": "user" + _AT + DOMAIN}}}
        email: EmailStr = Field(description=_DESC_FIELD_EMAIL_REQ)

    @router.get(
        _ROUTE_SESSION,
        response_model=_SessionResponse,
        summary="Get active session",
        description=_DESC_GET_SESSION,
        response_description="Active session details.",
    )
    async def get_session(token: ApiToken = Depends(token_dependency)) -> _SessionResponse:
        email: Optional[str] = get_active_email(store, token.user_id)
        if email is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_ERR_NO_SESSION)
        return _SessionResponse(email=email, expires_in_minutes=_MINUTES)

    @router.delete(
        _ROUTE_SESSION,
        status_code=status.HTTP_204_NO_CONTENT,
        summary="Stop active session",
        description=_DESC_DELETE_SESSION,
        response_description="Session stopped. No content returned.",
    )
    async def delete_session(token: ApiToken = Depends(token_dependency)) -> None:
        if not stop_session(store, token.user_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_ERR_NO_SESSION)

    @router.post(
        _ROUTE_SESSION,
        response_model=_SessionResponse,
        status_code=status.HTTP_201_CREATED,
        summary="Register a specific address",
        description=_DESC_POST_SESSION,
        response_description="Newly created session details.",
    )
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

    @router.post(
        _ROUTE_SESSION_RANDOM,
        response_model=_SessionResponse,
        status_code=status.HTTP_201_CREATED,
        summary="Register a random address",
        description=_DESC_POST_SESSION_RANDOM,
        response_description="Newly created session details with the generated address.",
    )
    async def register_random(token: ApiToken = Depends(token_dependency)) -> _SessionResponse:
        try:
            local = generate_local(RANDOM_KEY, token.user_id, random_nonce())
        except OverflowError:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=_ERR_OVERFLOW)
        email = local + _AT + DOMAIN
        await register_session(store, token.user_id, email, SESSION_TTL_SECONDS)
        return _SessionResponse(email=email, expires_in_minutes=_MINUTES)

    @router.get(
        _ROUTE_MAIL_POLL,
        response_model=Optional[_MailMessageResponse],
        summary="Poll for incoming mail",
        description=_DESC_POLL,
        response_description="Received message, or null if the 30-second timeout elapsed.",
    )
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
