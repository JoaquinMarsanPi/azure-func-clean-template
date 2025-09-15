from typing import Optional
import os

try:
    from app.core.config import settings  # type: ignore
except Exception:  # pragma: no cover
    settings = None  # fallback 


try:
    from azure.identity import DefaultAzureCredential  # type: ignore
    from azure.keyvault.secrets import SecretClient  # type: ignore
except Exception:  # pragma: no cover
    DefaultAzureCredential = None  # type: ignore
    SecretClient = None  # type: ignore


class KeyVaultService:

    def __init__(self, vault_uri: Optional[str] = None) -> None:

        self._vault_uri: Optional[str] = (
            vault_uri
            or getattr(settings, "KEYVAULT_URI", None) if settings else None
            or os.getenv("KEYVAULT_URI")
        )
        self._client = None

        if self._vault_uri and DefaultAzureCredential and SecretClient:
            try:
                cred = DefaultAzureCredential(
                    exclude_interactive_browser_credential=False
                )
                self._client = SecretClient(vault_url=self._vault_uri, credential=cred)
            except Exception:

                self._client = None

    @property
    def is_configured(self) -> bool:
        return self._client is not None

    def get_secret(self, name: str, version: Optional[str] = None) -> Optional[str]:

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


_kv: Optional[KeyVaultService] = None


def get_kv() -> KeyVaultService:
    global _kv
    if _kv is None:
        _kv = KeyVaultService()
    return _kv
