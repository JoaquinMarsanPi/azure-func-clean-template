from typing import Optional
from dataclasses import asdict
from app.core.config import settings
from db.repository.client import get_client
from db.models import Conversation

# Repositorio de conversaciones con fallback en memoria si Cosmos no está disponible.
class ConversationRepository:
    _mem: dict[str, Conversation] = {}  # Almacenamiento local cuando no hay conexión

    def __init__(self) -> None:
        # Inicializa cliente y nombre de contenedor desde configuración.
        self.cosmos = get_client()
        self.container_name = settings.CONTAINER_CONV

    def get(self, cid: str) -> Optional[Conversation]:
        # Obtiene una conversación por id. Usa memoria si Cosmos no está configurado.
        if not self.cosmos.is_configured:
            return self._mem.get(cid)
        try:
            item = self.cosmos.read(self.container_name, cid)
            return Conversation(**item)
        except Exception:
            # Si no existe o hay error de lectura, retorna None.
            return None

    def upsert(self, c: Conversation) -> None:
        # Inserta o actualiza la conversación. En memoria si no hay Cosmos.
        if not self.cosmos.is_configured:
            self._mem[c.id] = c; return
        self.cosmos.upsert(self.container_name, asdict(c))

    def delete(self, cid: str) -> bool:
        # Elimina por id. True si se eliminó, False si no se encontró o falló.
        if not self.cosmos.is_configured:
            return self._mem.pop(cid, None) is not None
        try:
            self.cosmos.delete(self.container_name, cid)
            return True
        except Exception:
            return False
