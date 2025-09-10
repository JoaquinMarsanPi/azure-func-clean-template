from dataclasses import dataclass

@dataclass
class Conversation:
    id: str
    user_id: str
    last_message: str = ""
