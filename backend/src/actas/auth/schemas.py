from pydantic import BaseModel


class LoginRequest(BaseModel):
    correo: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: str
    correo: str
    nombre: str
    activo: bool
