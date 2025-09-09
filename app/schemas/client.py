from pydantic import BaseModel

# Example schema for client
class ClientSchema(BaseModel):
    name: str
    email: str