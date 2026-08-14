from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    ime: str = Field(min_length=1, max_length=100)
    prezime: str = Field(min_length=1, max_length=100)
    broj_mobitela: str = Field(min_length=3, max_length=50)
    email: EmailStr | None = None
    username: str | None = Field(default=None, max_length=100)
    password: str = Field(min_length=8, max_length=128)


class UserLogin(BaseModel):
    identifier: EmailStr | str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    ime: str
    prezime: str
    broj_mobitela: str
    email: EmailStr | None = None
    username: str | None = None
    rola_id: int
