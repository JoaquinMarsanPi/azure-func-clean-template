from __future__ import annotations
from typing import Any, Iterable, Optional
from azure.cosmos import CosmosClient, ContainerProxy, DatabaseProxy
from app.core.config import settings

class CosmosDBClient:
    _client: Optional[CosmosClient] = None  # singleton

    def __init__(self) -> None:
        if not (settings.COSMOS_URL and settings.COSMOS_KEY):
            return
        if CosmosDBClient._client is None:
            CosmosDBClient._client = CosmosClient(
                url=settings.COSMOS_URL, credential=settings.COSMOS_KEY
            )

    @property
    def is_configured(self) -> bool:
        return CosmosDBClient._client is not None

    def db(self) -> DatabaseProxy:
        assert self.is_configured, "Cosmos no configurado (COSMOS_URL/COSMOS_KEY)"
        return CosmosDBClient._client.get_database_client(settings.COSMOS_DB)  # type: ignore

    def container(self, name: str) -> ContainerProxy:
        return self.db().get_container_client(name)

    def read(self, container: str, id: str, pk: Optional[str] = None) -> dict[str, Any]:
        c = self.container(container)
        return c.read_item(item=id, partition_key=pk or id)

    def upsert(self, container: str, item: dict[str, Any]) -> dict[str, Any]:
        c = self.container(container)
        return c.upsert_item(item)

    def delete(self, container: str, id: str, pk: Optional[str] = None) -> None:
        c = self.container(container)
        c.delete_item(item=id, partition_key=pk or id)

    def query(self, container: str, sql: str, params: Optional[list[dict[str, Any]]] = None) -> Iterable[dict[str, Any]]:
        c = self.container(container)
        return c.query_items(query=sql, parameters=params or [], enable_cross_partition_query=True)

_cosmos: Optional[CosmosDBClient] = None
def get_client() -> CosmosDBClient:
    global _cosmos
    if _cosmos is None:
        _cosmos = CosmosDBClient()
    return _cosmos
