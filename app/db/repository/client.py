from __future__ import annotations
from typing import Any, Iterable, Optional
import os

# SDK de Cosmos
from azure.cosmos import CosmosClient, ContainerProxy, DatabaseProxy
from app.core.config import settings

# Acceso opcional a Key Vault para obtener la clave si no está en env
try:
    from app.core.security import get_kv  # type: ignore
except Exception:  # pragma: no cover
    get_kv = None  # type: ignore


class CosmosDBClient:
    """
    Singleton ligero que expone operaciones mínimas (read/upsert/delete/query)
    sobre un CosmosClient ya inicializado.
    """
    _client: Optional[CosmosClient] = None  # instancia compartida

    def __init__(self) -> None:
        # Lee la URL y la clave de settings (o .env). La clave puede llegar vacía.
        url = settings.COSMOS_URL
        key = settings.COSMOS_KEY

        # Sin URL no es posible inicializar cliente.
        if not url:
            return

        # Intento obtener la clave desde Key Vault si no está en env.
        if not key and get_kv:
            try:
                kv = get_kv()
                if kv and kv.is_configured:
                    secret_name = getattr(settings, "COSMOS_KEY_SECRET_NAME", None) or os.getenv("COSMOS_KEY_SECRET_NAME")
                    if secret_name:
                        key_from_kv = kv.get_secret(secret_name)
                        if key_from_kv:
                            key = key_from_kv
            except Exception:
                # Si falla KV, seguimos con otros métodos de autenticación.
                pass

        # Reutiliza el cliente si ya fue creado previamente.
        if CosmosDBClient._client is not None:
            return

        client: Optional[CosmosClient] = None

        # 1) Preferencia: autenticar con clave (env o Key Vault).
        if key:
            client = CosmosClient(url=url, credential=key)
        else:
            # 2) Fallback: intentar AAD/Managed Identity.
            try:
                from azure.identity import DefaultAzureCredential  # type: ignore
                credential = DefaultAzureCredential(
                    exclude_interactive_browser_credential=False
                )
                client = CosmosClient(url=url, credential=credential)
            except Exception:
                # Sin clave ni AAD, el cliente queda no configurado.
                client = None

        CosmosDBClient._client = client

    @property
    def is_configured(self) -> bool:
        """Indica si existe un CosmosClient listo para usarse."""
        return CosmosDBClient._client is not None

    def db(self) -> DatabaseProxy:
        """Devuelve el DatabaseProxy según settings.COSMOS_DB (requiere cliente configurado)."""
        assert self.is_configured, "Cosmos no configurado (faltan credenciales)"
        return CosmosDBClient._client.get_database_client(settings.COSMOS_DB)  # type: ignore

    def container(self, name: str) -> ContainerProxy:
        """Obtiene un ContainerProxy por nombre."""
        return self.db().get_container_client(name)

    def read(self, container: str, id: str, pk: Optional[str] = None) -> dict[str, Any]:
        """
        Lee un item por id.
        Nota: por defecto usa partition_key=id salvo que se provea pk explícita.
        """
        c = self.container(container)
        return c.read_item(item=id, partition_key=(pk if pk is not None else id))

    def upsert(self, container: str, item: dict[str, Any]) -> dict[str, Any]:
        """Inserta/actualiza un item."""
        c = self.container(container)
        return c.upsert_item(item)

    def delete(self, container: str, id: str, pk: Optional[str] = None) -> None:
        """Elimina un item por id (con pk opcional)."""
        c = self.container(container)
        c.delete_item(item=id, partition_key=(pk if pk is not None else id))

    def query(
        self,
        container: str,
        sql: str,
        params: Optional[list[dict[str, Any]]] = None,
    ) -> Iterable[dict[str, Any]]:
        """
        Ejecuta una query SQL sobre el contenedor con parámetros opcionales.
        Habilita cross-partition por defecto.
        """
        c = self.container(container)
        return c.query_items(
            query=sql,
            parameters=(params or []),
            enable_cross_partition_query=True,
        )


# Singleton simple para obtener/reutilizar el cliente en toda la app.
_cosmos: Optional[CosmosDBClient] = None


def get_client() -> CosmosDBClient:
    global _cosmos
    if _cosmos is None:
        _cosmos = CosmosDBClient()
    return _cosmos