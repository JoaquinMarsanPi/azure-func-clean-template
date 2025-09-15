from dataclasses import asdict
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
import re
import uuid

from db.repository.resources import ResourceRepository
from db.repository.conversations import ConversationRepository
from db.repository.blocked import BlockedRepository

from db.models import Resource, Conversation, BlockedItem

_DEFAULT_PERSONALITY = "default_personality"
_DEFAULT_ANSWER = "default_answer"
_PROMPT_KIND = "prompt"


def _prompt_id(name: str) -> str:
    return f"{_PROMPT_KIND}:{name}"


class DBService:
    def __init__(self):
        self.resource_repo = ResourceRepository()
        self.conversation_repo = ConversationRepository()
        self.blocked_repo = BlockedRepository()

        self._blocked_cache: List[BlockedItem] = []
        self._blocked_pattern: Optional[re.Pattern] = None
        self._warmup_blocked()

    # Resources
    def set_prompt(self, name: str, text: str) -> dict:
        if not name:
            raise ValueError("'name' is required")
        rid = _prompt_id(name)
        res = Resource(id=rid, name=name, kind=_PROMPT_KIND, content=text)
        self.resource_repo.upsert(res)
        return asdict(res)

    def get_prompt(self, name: str) -> Optional[str]:
        rid = _prompt_id(name)
        res = self.resource_repo.get(rid)
        return getattr(res, "content", None) if res else None

    def get_default_personality_prompt(self) -> Optional[str]:
        return self.get_prompt(_DEFAULT_PERSONALITY)

    def get_default_answer_prompt(self) -> Optional[str]:
        return self.get_prompt(_DEFAULT_ANSWER)

    def upsert_resource(
        self,
        *,
        id: str,
        name: str,
        kind: str = "generic",
        content: Optional[str] = None
    ) -> dict:
        if not id or not name:
            raise ValueError("'id' and 'name' are required")
        if len(id) > 128:
            raise ValueError("'id' exceeds maximum length of 128 characters")
        resource = Resource(id=id, name=name, kind=kind, content=content)
        self.resource_repo.upsert(resource)
        return asdict(resource)

    def get_resource(self, id: str) -> Optional[dict]:
        resource = self.resource_repo.get(id)
        return asdict(resource) if resource else None

    def delete_resource(self, id: str) -> bool:
        return self.resource_repo.delete(id)

    # Conversations

    def create_conversation(self, *, user_id: str, id: Optional[str] = None) -> dict:
        if not user_id:
            raise ValueError("'user_id' is required")

        conv_id = id or uuid.uuid4().hex
        convo = Conversation(id=conv_id, user_id=user_id, last_message="")

        if hasattr(convo, "messages") and getattr(convo, "messages") is None:
            setattr(convo, "messages", [])

        if hasattr(convo, "updated_at"):
            setattr(convo, "updated_at", datetime.now(timezone.utc).isoformat())

        self.conversation_repo.upsert(convo)
        return asdict(convo)

    def append_message(
        self,
        *,
        conversation_id: str,
        role: str,            # "user" | "assistant" | "system"
        content: str,
        meta: Optional[Dict[str, Any]] = None
    ) -> dict:

        if not conversation_id:
            raise ValueError("'conversation_id' is required")
        if role not in ("user", "assistant", "system"):
            raise ValueError("'role' must be one of: user|assistant|system")

        convo = self.conversation_repo.get(conversation_id)
        if not convo:
            raise ValueError(f"Conversation '{conversation_id}' not found")

        msg = {
            "role": role,
            "content": content,
            "meta": meta or {},
            "ts": datetime.now(timezone.utc).isoformat(),
        }

        if hasattr(convo, "messages") and isinstance(getattr(convo, "messages"), list):
            convo.messages.append(msg)  # type: ignore[attr-defined]

        if hasattr(convo, "last_message"):
            convo.last_message = content  # type: ignore[attr-defined]

        if hasattr(convo, "updated_at"):
            setattr(convo, "updated_at", datetime.now(timezone.utc).isoformat())

        self.conversation_repo.upsert(convo)
        return msg

    def get_history(self, conversation_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Devuelve los últimos N mensajes de la conversación.
        Si el modelo no tiene 'messages', devuelve fallback con last_message (si existe).
        """
        convo = self.conversation_repo.get(conversation_id)
        if not convo:
            return []

        if hasattr(convo, "messages") and isinstance(getattr(convo, "messages"), list):
            msgs: List[Dict[str, Any]] = getattr(convo, "messages")  # type: ignore[assignment]
            if limit is not None and limit > 0:
                return msgs[-limit:]
            return msgs

        if hasattr(convo, "last_message") and getattr(convo, "last_message"):
            return [{"role": "unknown", "content": getattr(convo, "last_message")}]

        return []

    def get_conversation(self, id: str) -> Optional[dict]:
        conversation = self.conversation_repo.get(id)
        return asdict(conversation) if conversation else None

    # Blocked list

    def _warmup_blocked(self):

        if hasattr(self.blocked_repo, "get_all"):
            try:
                items = self.blocked_repo.get_all()  # type: ignore[attr-defined]
                self._blocked_cache = items or []
            except Exception:
                self._blocked_cache = []
        self._blocked_pattern = self._compile_blocked(self._blocked_cache)

    @staticmethod
    def _compile_blocked(items: List[BlockedItem]) -> Optional[re.Pattern]:
        terms = [re.escape(i.id) for i in items if getattr(i, "id", None)]
        if not terms:
            return None
        return re.compile("(" + "|".join(terms) + ")", flags=re.IGNORECASE)

    def is_text_allowed(self, text: str) -> tuple[bool, List[str]]:
        if not text:
            return True, []
        if not self._blocked_pattern:
            return True, []
        matches = sorted(set(m.group(0) for m in self._blocked_pattern.finditer(text)))
        return (len(matches) == 0), matches

    def list_blocked_terms(self) -> List[str]:
        return sorted([i.id for i in self._blocked_cache])

    def block_word(self, *, word: str, reason: str = "") -> dict:
        if not word:
            raise ValueError("'word' is required")
        item = BlockedItem(id=word, reason=reason)
        self.blocked_repo.upsert(item)

        found = next((i for i in self._blocked_cache if i.id.lower() == word.lower()), None)
        if not found:
            self._blocked_cache.append(item)
        else:
            found.reason = reason

        self._blocked_pattern = self._compile_blocked(self._blocked_cache)
        return asdict(item)

    def unblock_word(self, word: str) -> bool:
        ok = self.blocked_repo.delete(word)
        if ok:
            self._blocked_cache = [i for i in self._blocked_cache if i.id.lower() != word.lower()]
            self._blocked_pattern = self._compile_blocked(self._blocked_cache)
        return ok

    def validate_conversation_content(self, conversation_id: str) -> Optional[dict]:
        convo = self.conversation_repo.get(conversation_id)
        if not convo:
            return None

        matches: List[str] = []
        if self._blocked_pattern and getattr(convo, "last_message", None):
            matches = sorted(set(m.group(0) for m in self._blocked_pattern.finditer(convo.last_message)))  # type: ignore[arg-type]

        return {
            "conversation": asdict(convo),
            "contains_blocked_words": bool(matches),
            "matches": matches,
        }
