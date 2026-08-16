from decimal import Decimal
from datetime import datetime

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


class KlijentCreate(BaseModel):
    ime: str = Field(min_length=1, max_length=100)
    prezime: str = Field(min_length=1, max_length=100)
    broj_mobitela: str = Field(min_length=3, max_length=50)
    email: EmailStr | str | None = None


class KlijentCreateResponse(BaseModel):
    status: str = "success"
    klijent_id: int
    poruka: str = "Brzi profil klijenta uspješno kreiran."


class UserRoleUpdate(BaseModel):
    rola_id: int = Field(ge=1, le=2)


class UslugaCreate(BaseModel):
    naziv: str = Field(min_length=1, max_length=150)
    trajanje: int = Field(gt=0)
    cijena: Decimal = Field(ge=0)


class UslugaOut(BaseModel):
    id: int
    naziv: str
    trajanje: int
    cijena: Decimal


class UslugaCreateResponse(BaseModel):
    status: str = "success"
    usluga_id: int
    poruka: str = "Usluga uspješno kreirana."


class UslugaUpdate(BaseModel):
    naziv: str = Field(min_length=1, max_length=150)
    trajanje: int = Field(gt=0)
    cijena: Decimal = Field(ge=0)


class RadnoVrijemeCreate(BaseModel):
    vrijeme_od: datetime
    vrijeme_do: datetime


class RadnoVrijemeOut(BaseModel):
    id: int
    vrijeme_od: datetime
    vrijeme_do: datetime


class RezervacijaCreate(BaseModel):
    pocetak: datetime
    kraj: datetime
    usluga_id: int = Field(gt=0)
    klijent_id: int = Field(gt=0)
    biljeska: str | None = None


class RezervacijaOut(BaseModel):
    id: int
    pocetak: datetime
    kraj: datetime
    biljeska: str | None = None
    usluga_id: int
    klijent_id: int
    status_id: int


class RezervacijaCreateResponse(BaseModel):
    status: str = "success"
    rezervacija_id: int
    poruka: str = "Rezervacija uspješno kreirana."


class RecenzijaCreate(BaseModel):
    ocjena: int = Field(ge=1, le=5)
    rezervacija_id: int = Field(gt=0)
    usluga_id: int = Field(gt=0)
    klijent_id: int = Field(gt=0)
    komentar: str | None = None


class RecenzijaOut(BaseModel):
    id: int
    ocjena: int
    komentar: str | None = None
    rezervacija_id: int
    usluga_id: int
    klijent_id: int


class RecenzijaCreateResponse(BaseModel):
    status: str = "success"
    recenzija_id: int
    poruka: str = "Recenzija uspješno kreirana."
