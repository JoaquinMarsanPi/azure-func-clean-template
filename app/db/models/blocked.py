from dataclasses import dataclass

@dataclass
class BlockedItem:
    id: str
    reason: str = ""
