from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models_orm import Recenzija


async def create_recenzija_async(
    session: AsyncSession,
    ocjena: int,
    rezervacija_id: int,
    usluga_id: int,
    klijent_id: int,
    komentar: Optional[str] = None,
) -> dict:
    obj = Recenzija(
        ocjena=ocjena,
        komentar=komentar,
        rezervacija_id=rezervacija_id,
        usluga_id=usluga_id,
        klijent_id=klijent_id,
    )
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return {
        "id": obj.id,
        "ocjena": obj.ocjena,
        "komentar": obj.komentar,
        "rezervacija_id": obj.rezervacija_id,
        "usluga_id": obj.usluga_id,
        "klijent_id": obj.klijent_id,
    }


async def list_recenzije_for_usluga_async(session: AsyncSession, usluga_id: int) -> list[dict]:
    q = select(Recenzija).where(Recenzija.usluga_id == usluga_id).order_by(Recenzija.id.desc())
    result = await session.execute(q)
    rows = result.scalars().all()
    return [
        {
            "id": row.id,
            "ocjena": row.ocjena,
            "komentar": row.komentar,
            "rezervacija_id": row.rezervacija_id,
            "usluga_id": row.usluga_id,
            "klijent_id": row.klijent_id,
        }
        for row in rows
    ]
