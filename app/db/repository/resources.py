from typing import Optional
from dataclasses import asdict
from app.core.config import settings
from db.repository.client import get_client
from db.models import Resource

class ResourceRepository:
    _mem: dict[str, Resource] = {}

    def __init__(self) -> None:
        self.cosmos = get_client()
        self.container_name = settings.CONTAINER_RES

    def get(self, rid: str) -> Optional[Resource]:
        if not self.cosmos.is_configured:
            return self._mem.get(rid)
        try:
            item = self.cosmos.read(self.container_name, rid)
            return Resource(**item)
        except Exception:
            return None

    def upsert(self, r: Resource) -> None:
        if not self.cosmos.is_configured:
            self._mem[r.id] = r; return
        self.cosmos.upsert(self.container_name, asdict(r))

    def delete(self, rid: str) -> bool:
        if not self.cosmos.is_configured:
            return self._mem.pop(rid, None) is not None
        try:
            self.cosmos.delete(self.container_name, rid)
            return True
        except Exception:
            return False
