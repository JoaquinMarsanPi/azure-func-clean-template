from typing import Optional
from dataclasses import asdict
from app.core.config import settings
from db.repository.client import get_client
from db.models import BlockedItem

# Repositorio de términos bloqueados con fallback en memoria si Cosmos no está disponible.
class BlockedRepository:
    _mem: dict[str, BlockedItem] = {}  # Almacenamiento en memoria (modo local/desconfigurado)

    def __init__(self) -> None:
        # Inicializa el cliente y fija el contenedor desde configuración.
        self.cosmos = get_client()
        self.container_name = settings.CONTAINER_BLOCK

    def get(self, bid: str) -> Optional[BlockedItem]:
        # Recupera un término por id. En memoria si Cosmos no está configurado.
        if not self.cosmos.is_configured:
            return self._mem.get(bid)
        try:
            item = self.cosmos.read(self.container_name, bid)
            return BlockedItem(**item)
        except Exception:
            # Si no existe o hay error de lectura, retorna None.
            return None

    def upsert(self, b: BlockedItem) -> None:
        # Inserta/actualiza el término. Usa memoria si Cosmos no está configurado.
        if not self.cosmos.is_configured:
            self._mem[b.id] = b; return
        self.cosmos.upsert(self.container_name, asdict(b))

    def delete(self, bid: str) -> bool:
        # Elimina por id. Devuelve True si se eliminó, False en caso contrario.
        if not self.cosmos.is_configured:
            return self._mem.pop(bid, None) is not None
        try:
            self.cosmos.delete(self.container_name, bid)
            return True
        except Exception:
            return False
