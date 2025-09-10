# db/models/resource.py
from dataclasses import dataclass

@dataclass
class Resource:
    id: str
    name: str
    kind: str = "generic"
