from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app import models
from app.database import test_connection
from app.db import get_async_session
from app.repos import (
    create_korisnik_async,
    get_korisnik_by_email_async,
    get_korisnik_by_username_async,
)
from app.security import hash_password, verify_password, create_access_token


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="ZrinkaApp API", lifespan=lifespan)


@app.get("/health")
def health_check() -> dict[str, str | bool]:
    return {"status": "ok", "database": test_connection()}


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "ZrinkaApp API is running"}


@app.post("/users", response_model=models.UserOut, status_code=status.HTTP_201_CREATED)
async def register_user(payload: models.UserCreate, session: AsyncSession = Depends(get_async_session)) -> dict:
    if payload.email is not None and await get_korisnik_by_email_async(session, payload.email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="email_already_registered")
    if payload.username is not None and await get_korisnik_by_username_async(session, payload.username):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="username_already_registered")

    hashed = hash_password(payload.password)
    created = await create_korisnik_async(
        session,
        ime=payload.ime,
        prezime=payload.prezime,
        broj_mobitela=payload.broj_mobitela,
        email=payload.email,
        username=payload.username,
        password_hash=hashed,
    )
    return created


@app.post("/token", response_model=models.TokenResponse)
async def login(payload: models.UserLogin, session: AsyncSession = Depends(get_async_session)) -> dict:
    identifier = payload.identifier.strip()
    user = await get_korisnik_by_email_async(session, identifier)
    if user is None:
        user = await get_korisnik_by_username_async(session, identifier)
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_credentials")

    token = create_access_token(subject=str(user["id"]))
    return {"access_token": token, "token_type": "bearer"}
