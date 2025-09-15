from __future__ import annotations
from typing import Any, Iterable, Optional
import os

from azure.cosmos import CosmosClient, ContainerProxy, DatabaseProxy
from app.core.config import settings

try:
    from app.core.security import get_kv  # type: ignore
except Exception:  # pragma: no cover
    get_kv = None  # type: ignore


class CosmosDBClient:
    _client: Optional[CosmosClient] = None  # singleton

    def __init__(self) -> None:
        url = settings.COSMOS_URL
        key = settings.COSMOS_KEY  

        if not url:
            return

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
                pass

        if CosmosDBClient._client is not None:
            return

        client: Optional[CosmosClient] = None

        if key:
            client = CosmosClient(url=url, credential=key)
        else:
            try:
                from azure.identity import DefaultAzureCredential  # type: ignore
                credential = DefaultAzureCredential(
                    exclude_interactive_browser_credential=False
                )
                client = CosmosClient(url=url, credential=credential)
            except Exception:
                client = None 

        CosmosDBClient._client = client

    @property
    def is_configured(self) -> bool:
        return CosmosDBClient._client is not None

    def db(self) -> DatabaseProxy:
        assert self.is_configured, "Cosmos no configurado (faltan credenciales)"
        return CosmosDBClient._client.get_database_client(settings.COSMOS_DB)  # type: ignore

    def container(self, name: str) -> ContainerProxy:
        return self.db().get_container_client(name)

    def read(self, container: str, id: str, pk: Optional[str] = None) -> dict[str, Any]:
        c = self.container(container)
        return c.read_item(item=id, partition_key=(pk if pk is not None else id))

    def upsert(self, container: str, item: dict[str, Any]) -> dict[str, Any]:
        c = self.container(container)
        return c.upsert_item(item)

    def delete(self, container: str, id: str, pk: Optional[str] = None) -> None:
        c = self.container(container)
        c.delete_item(item=id, partition_key=(pk if pk is not None else id))

    def query(
        self,
        container: str,
        sql: str,
        params: Optional[list[dict[str, Any]]] = None,
    ) -> Iterable[dict[str, Any]]:
        c = self.container(container)
        return c.query_items(
            query=sql,
            parameters=(params or []),
            enable_cross_partition_query=True,
        )


_cosmos: Optional[CosmosDBClient] = None


def get_client() -> CosmosDBClient:
    global _cosmos
    if _cosmos is None:
        _cosmos = CosmosDBClient()
    return _cosmos
