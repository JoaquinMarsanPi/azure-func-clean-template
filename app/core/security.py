from typing import Optional
import os

# Carga opcional de settings (el módulo puede funcionar sin él).
try:
    from app.core.config import settings  # type: ignore
except Exception:  # pragma: no cover
    settings = None

# Importación opcional de SDKs de Azure; si no están, el servicio queda no configurado.
try:
    from azure.identity import DefaultAzureCredential  # type: ignore
    from azure.keyvault.secrets import SecretClient  # type: ignore
except Exception:  # pragma: no cover
    DefaultAzureCredential = None  # type: ignore
    SecretClient = None  # type: ignore


class KeyVaultService:
    # Wrapper liviano sobre SecretClient: resuelve el vault URI y expone get_secret().

    def __init__(self, vault_uri: Optional[str] = None) -> None:
        # Prioridad para el origen del URI: parámetro > settings.KEYVAULT_URI > env KEYVAULT_URI.
        self._vault_uri: Optional[str] = (
            vault_uri
            or getattr(settings, "KEYVAULT_URI", None) if settings else None
            or os.getenv("KEYVAULT_URI")
        )
        self._client = None

        # Inicializa SecretClient sólo si hay URI y SDKs disponibles.
        if self._vault_uri and DefaultAzureCredential and SecretClient:
            try:
                cred = DefaultAzureCredential(
                    exclude_interactive_browser_credential=False
                )
                self._client = SecretClient(vault_url=self._vault_uri, credential=cred)
            except Exception:
                # Si falla la credencial o la creación del cliente, se mantiene no configurado.
                self._client = None

    @property
    def is_configured(self) -> bool:
        # Indica si el cliente de Key Vault está disponible para usarse.
        return self._client is not None

    def get_secret(self, name: str, version: Optional[str] = None) -> Optional[str]:
        # Obtiene el valor de un secreto por nombre (y versión opcional).
        # Devuelve None si no está configurado, no existe o hay error de acceso.
        if not self.is_configured or not name:
            return None
        try:
            if version:
                sec = self._client.get_secret(name, version=version)  # type: ignore[attr-defined]
            else:
                sec = self._client.get_secret(name)  # type: ignore[attr-defined]
            return getattr(sec, "value", None)
        except Exception:
            return None


# Singleton básico para reutilizar la misma instancia del servicio.
_kv: Optional[KeyVaultService] = None


def get_kv() -> KeyVaultService:
    global _kv
    if _kv is None:
        _kv = KeyVaultService()
    return _kv