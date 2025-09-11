from db.repository.resources import ResourceRepository
from db.repository.conversations import ConversationRepository
from db.repository.blocked import BlockedRepository
from db.models import Resource, Conversation, BlockedItem
from dataclasses import asdict

class DBService:
    def __init__(self):
        # Initialize repositories for resources, conversations, and blocked users
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

    def set_conversation_last_message(self, *, id: str, text: str) -> dict | None:
        # Update the last message of a conversation
        conversation = self.conversation_repo.get(id)
        if not conversation:
            return None
        conversation.last_message = text
        self.conversation_repo.upsert(conversation)
        return asdict(conversation)

    def delete_conversation(self, id: str) -> bool:
        # Delete a conversation by ID
        return self.conversation_repo.delete(id)

    # Blocked
    def is_blocked(self, user_id: str) -> bool:
        # Check if a user is blocked
        blocked = self.blocked_repo.get(user_id)
        return blocked is not None

    def block_user(self, *, user_id: str, reason: str = "") -> dict:
        # Block a user with an optional reason
        if not user_id:
            raise ValueError("'user_id' is required")
        blocked_item = BlockedItem(id=user_id, reason=reason)
        self.blocked_repo.upsert(blocked_item)
        return asdict(blocked_item)

    def unblock_user(self, user_id: str) -> bool:
        # Unblock a user by ID
        return self.blocked_repo.delete(user_id)
