from pydantic import BaseModel

class TokenPayload(BaseModel):
    sub: str
    email: str | None = None
    role: str | None = None
