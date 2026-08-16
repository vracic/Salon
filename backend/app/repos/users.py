from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models_orm import Korisnik


async def create_korisnik_async(
    session: AsyncSession,
    ime: str,
    prezime: str,
    broj_mobitela: str,
    email: Optional[str],
    username: Optional[str],
    password_hash: str,
) -> dict:
    obj = Korisnik(
        ime=ime,
        prezime=prezime,
        broj_mobitela=broj_mobitela,
        email=email,
        username=username,
        password_hash=password_hash,
    )
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return {
        "id": obj.id,
        "ime": obj.ime,
        "prezime": obj.prezime,
        "broj_mobitela": obj.broj_mobitela,
        "email": obj.email,
        "username": obj.username,
        "rola_id": obj.rola_id,
    }


async def get_korisnik_by_email_async(session: AsyncSession, email: str) -> Optional[dict]:
    q = select(Korisnik).where(Korisnik.email == email)
    result = await session.execute(q)
    row = result.scalar_one_or_none()
    if row is None:
        return None
    return {
        "id": row.id,
        "ime": row.ime,
        "prezime": row.prezime,
        "broj_mobitela": row.broj_mobitela,
        "email": row.email,
        "username": row.username,
        "password_hash": row.password_hash,
        "rola_id": row.rola_id,
    }


async def get_korisnik_by_username_async(session: AsyncSession, username: str) -> Optional[dict]:
    q = select(Korisnik).where(Korisnik.username == username)
    result = await session.execute(q)
    row = result.scalar_one_or_none()
    if row is None:
        return None
    return {
        "id": row.id,
        "ime": row.ime,
        "prezime": row.prezime,
        "broj_mobitela": row.broj_mobitela,
        "email": row.email,
        "username": row.username,
        "password_hash": row.password_hash,
        "rola_id": row.rola_id,
    }


async def get_korisnik_by_id_async(session: AsyncSession, korisnik_id: int) -> Optional[dict]:
    q = select(Korisnik).where(Korisnik.id == korisnik_id)
    result = await session.execute(q)
    row = result.scalar_one_or_none()
    if row is None:
        return None
    return {
        "id": row.id,
        "ime": row.ime,
        "prezime": row.prezime,
        "broj_mobitela": row.broj_mobitela,
        "email": row.email,
        "username": row.username,
        "rola_id": row.rola_id,
    }


async def create_klijent_async(
    session: AsyncSession,
    ime: str,
    prezime: str,
    broj_mobitela: str,
    email: Optional[str] = None,
) -> dict:
    obj = Korisnik(
        ime=ime,
        prezime=prezime,
        broj_mobitela=broj_mobitela,
        email=email,
        username=None,
        password_hash=None,
        rola_id=2,
    )
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return {
        "id": obj.id,
        "ime": obj.ime,
        "prezime": obj.prezime,
        "broj_mobitela": obj.broj_mobitela,
        "email": obj.email,
        "username": obj.username,
        "rola_id": obj.rola_id,
    }


async def update_korisnik_rola_async(session: AsyncSession, korisnik_id: int, rola_id: int) -> dict:
    row = await get_korisnik_by_id_async(session, korisnik_id)
    if row is None:
        raise ValueError("korisnik_not_found")

    result = await session.execute(select(Korisnik).where(Korisnik.id == korisnik_id))
    obj = result.scalar_one()
    obj.rola_id = rola_id
    await session.commit()
    await session.refresh(obj)
    return {
        "id": obj.id,
        "ime": obj.ime,
        "prezime": obj.prezime,
        "rola_id": obj.rola_id,
    }
