from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models_orm import Usluga


async def get_usluge_async(session: AsyncSession) -> list[dict]:
    q = select(Usluga).order_by(Usluga.id.asc())
    result = await session.execute(q)
    rows = result.scalars().all()
    return [
        {
            "id": row.id,
            "naziv": row.naziv,
            "trajanje": row.trajanje,
            "cijena": row.cijena,
        }
        for row in rows
    ]


async def create_usluga_async(
    session: AsyncSession,
    naziv: str,
    trajanje: int,
    cijena: Decimal,
) -> dict[str, Any]:
    obj = Usluga(naziv=naziv, trajanje=trajanje, cijena=cijena)
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return {
        "id": obj.id,
        "naziv": obj.naziv,
        "trajanje": obj.trajanje,
        "cijena": obj.cijena,
    }


async def update_usluga_async(
    session: AsyncSession,
    usluga_id: int,
    naziv: str,
    trajanje: int,
    cijena: Decimal,
) -> dict[str, Any]:
    result = await session.execute(select(Usluga).where(Usluga.id == usluga_id))
    obj = result.scalar_one_or_none()
    if obj is None:
        raise ValueError("usluga_not_found")

    obj.naziv = naziv
    obj.trajanje = trajanje
    obj.cijena = cijena
    await session.commit()
    await session.refresh(obj)
    return {
        "id": obj.id,
        "naziv": obj.naziv,
        "trajanje": obj.trajanje,
        "cijena": obj.cijena,
    }


async def delete_usluga_async(session: AsyncSession, usluga_id: int) -> None:
    result = await session.execute(select(Usluga).where(Usluga.id == usluga_id))
    obj = result.scalar_one_or_none()
    if obj is None:
        raise ValueError("usluga_not_found")

    await session.delete(obj)
    await session.commit()
