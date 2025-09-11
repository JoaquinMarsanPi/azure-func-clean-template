from db.repository.resources import ResourceRepository
from db.repository.conversations import ConversationRepository
from db.repository.blocked import BlockedRepository
from db.models import Resource, Conversation, BlockedWord
from dataclasses import asdict

class DBService:
    def __init__(self):
        # Initialize repositories for resources, conversations, and blocked words
        self.resource_repo = ResourceRepository()
        self.conversation_repo = ConversationRepository()
        self.blocked_repo = BlockedRepository()

    # Resources
    def upsert_resource(self, *, id: str, name: str, kind: str = "generic") -> dict:
        # Validate input and upsert a resource
        if not id or not name:
            raise ValueError("'id' and 'name' are required")
        if len(id) > 128:
            raise ValueError("'id' exceeds maximum length of 128 characters")
        resource = Resource(id=id, name=name, kind=kind)
        self.resource_repo.upsert(resource)
        return asdict(resource)

    def get_resource(self, id: str) -> dict | None:
        # Retrieve a resource by ID
        resource = self.resource_repo.get(id)
        return asdict(resource) if resource else None

    def delete_resource(self, id: str) -> bool:
        # Delete a resource by ID
        return self.resource_repo.delete(id)

    # Conversations
    def upsert_conversation(self, *, id: str, user_id: str, last_message: str = "") -> dict:
        # Validate input and upsert a conversation
        if not id or not user_id:
            raise ValueError("'id' and 'user_id' are required")
        conversation = Conversation(id=id, user_id=user_id, last_message=last_message)
        self.conversation_repo.upsert(conversation)
        return asdict(conversation)

    def get_conversation(self, id: str) -> dict | None:
        # Retrieve a conversation by ID
        conversation = self.conversation_repo.get(id)
        return asdict(conversation) if conversation else None

    def validate_conversation(self, id: str) -> dict | None:
        # Retrieve a conversation and validate its content against blocked words
        conversation = self.conversation_repo.get(id)
        if not conversation:
            return None

        # Check if the conversation contains blocked words
        blocked_words = [word.id for word in self.blocked_repo.get_all()]
        contains_blocked = any(word in conversation.last_message for word in blocked_words)

        return {
            "conversation": asdict(conversation),
            "contains_blocked_words": contains_blocked
        }

    def delete_conversation(self, id: str) -> bool:
        # Delete a conversation by ID
        return self.conversation_repo.delete(id)

    # Blocked Words
    def is_blocked_word(self, word: str) -> bool:
        # Check if a word is blocked
        blocked = self.blocked_repo.get(word)
        return blocked is not None

    def block_word(self, *, word: str, reason: str = "") -> dict:
        # Block a word with an optional reason
        if not word:
            raise ValueError("'word' is required")
        blocked_word = BlockedWord(id=word, reason=reason)
        self.blocked_repo.upsert(blocked_word)
        return asdict(blocked_word)

    def unblock_word(self, word: str) -> bool:
        # Unblock a word by ID
        return self.blocked_repo.delete(word)
