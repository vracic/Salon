from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    ime: str = Field(min_length=1, max_length=100)
    prezime: str = Field(min_length=1, max_length=100)
    broj_mobitela: str = Field(min_length=3, max_length=50)
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=8, max_length=72)
    email: EmailStr | str | None = None


class UserLogin(BaseModel):
    username: str
    password: str


class RegisterResponse(BaseModel):
    status: str = "success"
    poruka: str = "Registracija uspješna."
    token: str
    rola: str
    username: str
    ime: str


class LoginResponse(BaseModel):
    token: str
    rola: str
    username: str
    ime: str


class UserOut(BaseModel):
    id: int
    ime: str
    prezime: str
    broj_mobitela: str
    email: EmailStr | None = None
    username: str | None = None
    rola_id: int
