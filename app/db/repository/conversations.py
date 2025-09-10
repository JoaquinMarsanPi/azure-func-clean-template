from typing import Optional
from dataclasses import asdict
from app.core.config import settings
from db.repository.client import get_client
from db.models import Conversation

class ConversationRepository:
    _mem: dict[str, Conversation] = {}
    def __init__(self) -> None:
        self.cosmos = get_client()
        self.container_name = settings.CONTAINER_CONV

    def get(self, cid: str) -> Optional[Conversation]:
        if not self.cosmos.is_configured:
            return self._mem.get(cid)
        try:
            item = self.cosmos.read(self.container_name, cid)
            return Conversation(**item)
        except Exception:
            return None

    def upsert(self, c: Conversation) -> None:
        if not self.cosmos.is_configured:
            self._mem[c.id] = c; return
        self.cosmos.upsert(self.container_name, asdict(c))
