from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app import models
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
async def health_check(session: AsyncSession = Depends(get_async_session)) -> dict[str, str | bool]:
    try:
        await session.execute(text("SELECT 1"))
        return {"status": "ok", "database": True}
    except Exception:
        return {"status": "ok", "database": False}


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "ZrinkaApp API is running"}


@app.post("/api/auth/register", response_model=models.RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register_user(payload: models.UserCreate, session: AsyncSession = Depends(get_async_session)) -> dict:
    email_value = payload.email.strip() if isinstance(payload.email, str) and payload.email.strip() else None

    if email_value and await get_korisnik_by_email_async(session, email_value):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="email_already_registered")
    if await get_korisnik_by_username_async(session, payload.username):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="username_already_registered")

    hashed = hash_password(payload.password)
    created = await create_korisnik_async(
        session,
        ime=payload.ime,
        prezime=payload.prezime,
        broj_mobitela=payload.broj_mobitela,
        email=email_value,
        username=payload.username,
        password_hash=hashed,
    )

    token = create_access_token(subject=str(created["id"]))
    rola = "CUSTOMER"
    return {
        "status": "success",
        "poruka": "Registracija uspješna.",
        "token": token,
        "rola": rola,
        "username": created["username"],
        "ime": created["ime"],
    }


@app.post("/api/auth/login", response_model=models.LoginResponse)
async def login(payload: models.UserLogin, session: AsyncSession = Depends(get_async_session)) -> dict:
    user = await get_korisnik_by_username_async(session, payload.username)
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_credentials")

    token = create_access_token(subject=str(user["id"]))
    rola_name = "CUSTOMER" if user["rola_id"] == 2 else "ADMIN"
    return {
        "token": token,
        "rola": rola_name,
        "username": user["username"],
        "ime": user["ime"],
    }
