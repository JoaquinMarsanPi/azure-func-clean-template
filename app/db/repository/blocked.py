from typing import Optional
from dataclasses import asdict
from app.core.config import settings
from db.repository.client import get_client
from db.models import BlockedItem

class BlockedRepository:
    _mem: dict[str, BlockedItem] = {}
    def __init__(self) -> None:
        self.cosmos = get_client()
        self.container_name = settings.CONTAINER_BLOCK

    def get(self, bid: str) -> Optional[BlockedItem]:
        if not self.cosmos.is_configured:
            return self._mem.get(bid)
        try:
            item = self.cosmos.read(self.container_name, bid)
            return BlockedItem(**item)
        except Exception:
            return None

    def upsert(self, b: BlockedItem) -> None:
        if not self.cosmos.is_configured:
            self._mem[b.id] = b; return
        self.cosmos.upsert(self.container_name, asdict(b))

    def delete(self, bid: str) -> bool:
        if not self.cosmos.is_configured:
            return self._mem.pop(bid, None) is not None
        try:
            self.cosmos.delete(self.container_name, bid)
            return True
        except Exception:
            return False
