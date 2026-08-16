from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models_orm import RadnoVrijeme


async def create_radnovrijeme_async(
    session: AsyncSession,
    vrijeme_od: datetime,
    vrijeme_do: datetime,
) -> dict:
    obj = RadnoVrijeme(vrijeme_od=vrijeme_od, vrijeme_do=vrijeme_do)
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return {
        "id": obj.id,
        "vrijeme_od": obj.vrijeme_od,
        "vrijeme_do": obj.vrijeme_do,
    }


async def list_radnovrijeme_async(session: AsyncSession) -> list[dict]:
    q = select(RadnoVrijeme).order_by(RadnoVrijeme.vrijeme_od.asc())
    result = await session.execute(q)
    rows = result.scalars().all()
    return [
        {
            "id": row.id,
            "vrijeme_od": row.vrijeme_od,
            "vrijeme_do": row.vrijeme_do,
        }
        for row in rows
    ]
