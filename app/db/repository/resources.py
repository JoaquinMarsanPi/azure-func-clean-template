from typing import Optional
from dataclasses import asdict
from app.core.config import settings
from db.repository.client import get_client
from db.models import Resource

# Repositorio de recursos con fallback en memoria si Cosmos no está disponible.
class ResourceRepository:
    _mem: dict[str, Resource] = {}  # Almacenamiento local cuando no hay conexión

    def __init__(self) -> None:
        # Inicializa cliente y nombre de contenedor desde configuración.
        self.cosmos = get_client()
        self.container_name = settings.CONTAINER_RES

    def get(self, rid: str) -> Optional[Resource]:
        # Obtiene un recurso por id. Usa memoria si Cosmos no está configurado.
        if not self.cosmos.is_configured:
            return self._mem.get(rid)
        try:
            item = self.cosmos.read(self.container_name, rid)
            return Resource(**item)
        except Exception:
            # Si no existe o hay error de lectura, retorna None.
            return None

    def upsert(self, r: Resource) -> None:
        # Inserta o actualiza el recurso. En memoria si no hay Cosmos.
        if not self.cosmos.is_configured:
            self._mem[r.id] = r; return
        self.cosmos.upsert(self.container_name, asdict(r))

    def delete(self, rid: str) -> bool:
        # Elimina por id. True si se eliminó, False si no se encontró o falló.
        if not self.cosmos.is_configured:
            return self._mem.pop(rid, None) is not None
        try:
            self.cosmos.delete(self.container_name, rid)
            return True
        except Exception:
            return False
