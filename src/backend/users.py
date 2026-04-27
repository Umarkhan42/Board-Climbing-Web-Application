from pydantic import BaseModel

class RegisterRequest(BaseModel):
    email: str
    name: str | None = None

class LoginRequest(BaseModel):
    email: str

class SaveClimbRequest(BaseModel):
    name: str
    grade: str | None = None
    angle: int | None = None
    holds: list