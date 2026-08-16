from datetime import datetime
from typing import Optional

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models_orm import Rezervacija


async def has_overlapping_rezervacija_async(
    session: AsyncSession,
    pocetak: datetime,
    kraj: datetime,
) -> bool:
    q = select(Rezervacija.id).where(
        Rezervacija.status_id.in_([1, 2]),
        or_(
            and_(Rezervacija.pocetak <= pocetak, Rezervacija.kraj > pocetak),
            and_(Rezervacija.pocetak < kraj, Rezervacija.kraj >= kraj),
            and_(Rezervacija.pocetak >= pocetak, Rezervacija.kraj <= kraj),
        ),
    )
    result = await session.execute(q)
    return result.scalar_one_or_none() is not None


async def create_rezervacija_async(
    session: AsyncSession,
    pocetak: datetime,
    kraj: datetime,
    usluga_id: int,
    klijent_id: int,
    status_id: int = 1,
    biljeska: Optional[str] = None,
) -> dict:
    obj = Rezervacija(
        pocetak=pocetak,
        kraj=kraj,
        biljeska=biljeska,
        usluga_id=usluga_id,
        klijent_id=klijent_id,
        status_id=status_id,
    )
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return {
        "id": obj.id,
        "pocetak": obj.pocetak,
        "kraj": obj.kraj,
        "biljeska": obj.biljeska,
        "usluga_id": obj.usluga_id,
        "klijent_id": obj.klijent_id,
        "status_id": obj.status_id,
    }


async def get_rezervacija_by_id_async(session: AsyncSession, rezervacija_id: int) -> Optional[dict]:
    q = select(Rezervacija).where(Rezervacija.id == rezervacija_id)
    result = await session.execute(q)
    row = result.scalar_one_or_none()
    if row is None:
        return None
    return {
        "id": row.id,
        "pocetak": row.pocetak,
        "kraj": row.kraj,
        "biljeska": row.biljeska,
        "usluga_id": row.usluga_id,
        "klijent_id": row.klijent_id,
        "status_id": row.status_id,
    }


async def list_rezervacije_async(session: AsyncSession, klijent_id: Optional[int] = None) -> list[dict]:
    q = select(Rezervacija).order_by(Rezervacija.pocetak.asc())
    if klijent_id is not None:
        q = q.where(Rezervacija.klijent_id == klijent_id)
    result = await session.execute(q)
    rows = result.scalars().all()
    return [
        {
            "id": row.id,
            "pocetak": row.pocetak,
            "kraj": row.kraj,
            "biljeska": row.biljeska,
            "usluga_id": row.usluga_id,
            "klijent_id": row.klijent_id,
            "status_id": row.status_id,
        }
        for row in rows
    ]
