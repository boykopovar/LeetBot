import asyncio
import time
from dataclasses import dataclass, field
from typing import Dict, Optional

from src.domain.mail_message import MailMessage


@dataclass
class _Slot:
    event: asyncio.Event = field(default_factory=asyncio.Event)
    message: Optional[MailMessage] = None


class InMemoryMailbox:
    def __init__(self) -> None:
        self._slots: Dict[int, _Slot] = {}

    async def put(self, user_id: int, message: MailMessage) -> None:
        slot = self._slots.get(user_id)
        if slot is None:
            return
        slot.message = message
        slot.event.set()

    async def poll(self, user_id: int, deadline: float, timeout: float) -> Optional[MailMessage]:
        remaining = min(deadline - time.monotonic(), timeout)
        if remaining <= 0:
            return None
        slot = _Slot()
        self._slots[user_id] = slot
        try:
            await asyncio.wait_for(asyncio.shield(slot.event.wait()), timeout=remaining)
            return slot.message
        except asyncio.TimeoutError:
            return None
        finally:
            self._slots.pop(user_id, None)
