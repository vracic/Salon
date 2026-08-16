from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import Sequence, cast

from fastapi import FastAPI, HTTPException, status, Depends
from sqlalchemy import select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app import models
from app.db import get_async_session
from app.models_orm import KlijentBiljeska, Korisnik, Recenzija, Rezervacija, StatusRezervacija, Usluga
from app.repos import (
    create_klijent_async,
    create_radnovrijeme_async,
    create_recenzija_async,
    create_rezervacija_async,
    create_korisnik_async,
    create_usluga_async,
    delete_usluga_async,
    get_rezervacija_by_id_async,
    get_korisnik_by_email_async,
    get_korisnik_by_id_async,
    get_korisnik_by_username_async,
    has_overlapping_rezervacija_async,
    list_radnovrijeme_async,
    list_recenzije_for_usluga_async,
    list_rezervacije_async,
    get_usluge_async,
    update_korisnik_rola_async,
    update_usluga_async,
)
from app.security import hash_password, verify_password, create_access_token, get_current_user, require_admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="ZrinkaApp API", lifespan=lifespan)


def is_admin_user(user: dict | None) -> bool:
    return bool(user and user.get("rola_id") == 1)


def can_access_user_data(current_user: dict, target_user_id: int | None) -> bool:
    if is_admin_user(current_user):
        return True
    return target_user_id is not None and current_user.get("id") == target_user_id


def can_access_reservation(current_user: dict, reservation: dict | None) -> bool:
    if reservation is None:
        return False
    return is_admin_user(current_user) or current_user.get("id") == reservation.get("klijent_id")


def can_cancel_reservation(start: datetime, status_id: int, now: datetime | None = None) -> bool:
    if status_id == 3:
        return False
    reference_time = now or datetime.now(timezone.utc)
    return start > reference_time


def can_review_reservation(end: datetime, has_review: bool, now: datetime | None = None) -> bool:
    if has_review:
        return False
    reference_time = now or datetime.now(timezone.utc)
    return end <= reference_time


def build_available_starts(
    working_hours: Sequence[object],
    reservations: list[dict],
) -> list[str]:
    slots: list[str] = []
    if not working_hours:
        return slots

    intervals: list[tuple[datetime, datetime]] = []

    if len(working_hours) == 2 and all(isinstance(item, datetime) for item in working_hours):
        start_value = cast(datetime, working_hours[0])
        end_value = cast(datetime, working_hours[1])
        intervals.append((start_value, end_value))
    else:
        for item in working_hours:
            if isinstance(item, dict):
                start_value = item.get("vrijeme_od")
                end_value = item.get("vrijeme_do")
                if isinstance(start_value, datetime) and isinstance(end_value, datetime):
                    intervals.append((start_value, end_value))
            elif isinstance(item, tuple) and len(item) == 2:
                start_value, end_value = item
                if isinstance(start_value, datetime) and isinstance(end_value, datetime):
                    intervals.append((start_value, end_value))

    for start, end in intervals:
        current = start
        while current + timedelta(minutes=15) <= end:
            slot_start = current
            slot_end = current + timedelta(minutes=15)
            is_blocked = False
            for reservation in reservations:
                res_start = reservation["pocetak"]
                res_end = reservation["kraj"]
                if slot_start < res_end and res_start < slot_end:
                    is_blocked = True
                    break
            if not is_blocked:
                slots.append(slot_start.isoformat())
            current += timedelta(minutes=15)

    return slots


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


@app.get("/api/usluge", response_model=list[models.UslugaOut])
async def list_usluge(
    session: AsyncSession = Depends(get_async_session),
    current_user: dict = Depends(get_current_user),
) -> list[dict]:
    return await get_usluge_async(session)


@app.post("/api/usluge", response_model=models.UslugaCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_usluga(
    payload: models.UslugaCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user: dict = Depends(require_admin),
) -> dict:
    existing = await session.execute(
        select(
            Usluga
        ).where(Usluga.naziv == payload.naziv)
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="usluga_already_exists")

    created = await create_usluga_async(
        session,
        naziv=payload.naziv,
        trajanje=payload.trajanje,
        cijena=payload.cijena,
    )
    return {
        "status": "success",
        "usluga_id": created["id"],
        "poruka": "Usluga uspješno kreirana.",
    }


@app.put("/api/usluge/{usluga_id}", response_model=models.UslugaCreateResponse)
async def update_usluga(
    usluga_id: int,
    payload: models.UslugaUpdate,
    session: AsyncSession = Depends(get_async_session),
    current_user: dict = Depends(require_admin),
) -> dict:
    try:
        updated = await update_usluga_async(
            session,
            usluga_id=usluga_id,
            naziv=payload.naziv,
            trajanje=payload.trajanje,
            cijena=payload.cijena,
        )
    except ValueError as exc:
        if str(exc) == "usluga_not_found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="usluga_not_found") from exc
        raise

    return {
        "status": "success",
        "usluga_id": updated["id"],
        "poruka": "Usluga uspješno izmijenjena.",
    }


@app.delete("/api/usluge/{usluga_id}")
async def delete_usluga(
    usluga_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: dict = Depends(require_admin),
) -> dict:
    try:
        await delete_usluga_async(session, usluga_id)
    except ValueError as exc:
        if str(exc) == "usluga_not_found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="usluga_not_found") from exc
        raise
    return {
        "status": "success",
        "poruka": "Usluga uspješno obrisana iz kataloga.",
    }


@app.get("/api/radnovrijeme", response_model=list[models.RadnoVrijemeOut])
async def list_radnovrijeme(
    session: AsyncSession = Depends(get_async_session),
    current_user: dict = Depends(get_current_user),
) -> list[dict]:
    return await list_radnovrijeme_async(session)


@app.post("/api/radnovrijeme", response_model=models.RadnoVrijemeOut, status_code=status.HTTP_201_CREATED)
async def create_radnovrijeme(
    payload: models.RadnoVrijemeCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user: dict = Depends(require_admin),
) -> dict:
    if payload.vrijeme_do <= payload.vrijeme_od:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_time_range")
    return await create_radnovrijeme_async(session, payload.vrijeme_od, payload.vrijeme_do)


@app.put("/api/radnovrijeme/dan")
async def update_radnovrijeme_dan(
    payload: dict,
    session: AsyncSession = Depends(get_async_session),
    current_user: dict = Depends(require_admin),
) -> dict:
    if "datum" not in payload or "smjene" not in payload:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_payload")

    smjene = payload["smjene"]

    for smjena in smjene:
        if smjena["vrijeme_do"] <= smjena["vrijeme_od"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_time_range")

    day_start = datetime.fromisoformat(payload["datum"]).replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = day_start.replace(hour=23, minute=59, second=59, microsecond=999999)
    reservations_result = await session.execute(
        select(Rezervacija.id, Rezervacija.pocetak, Rezervacija.kraj).where(
            Rezervacija.pocetak >= day_start,
            Rezervacija.kraj <= day_end,
        )
    )
    conflicting = []
    for reservation_id, reservation_start, reservation_end in reservations_result.all():
        if not any(
            reservation_start < shift["vrijeme_do"] and shift["vrijeme_od"] < reservation_end
            for shift in smjene
        ):
            conflicting.append({
                "id": reservation_id,
                "pocetak": reservation_start,
                "kraj": reservation_end,
            })

    if conflicting:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "status": "error",
                "poruka": "Nemoguće ažurirati radno vrijeme. Postojeći termini ne staju u nove smjene.",
                "konfliktne_rezervacije": conflicting,
            },
        )

    await session.execute(text("DELETE FROM radnovrijeme"))
    for smjena in smjene:
        await create_radnovrijeme_async(
            session,
            vrijeme_od=smjena["vrijeme_od"],
            vrijeme_do=smjena["vrijeme_do"],
        )

    return {
        "status": "success",
        "poruka": "Raspored za izabrani dan je uspješno ažuriran.",
    }


@app.get("/api/rezervacije", response_model=list[models.RezervacijaOut])
async def list_rezervacije(
    klijent_id: int | None = None,
    session: AsyncSession = Depends(get_async_session),
    current_user: dict = Depends(get_current_user),
) -> list[dict]:
    if not is_admin_user(current_user):
        if klijent_id is not None and klijent_id != current_user["id"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
        klijent_id = current_user["id"]
    return await list_rezervacije_async(session, klijent_id=klijent_id)


@app.get("/api/rezervacije/slobodni-termini")
async def get_slobodni_termini(
    datum: str,
    session: AsyncSession = Depends(get_async_session),
    current_user: dict = Depends(get_current_user),
) -> dict:
    try:
        date_value = datetime.fromisoformat(datum)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_date") from exc

    radno_vrijeme = await list_radnovrijeme_async(session)
    reservations_result = await session.execute(
        select(Rezervacija.pocetak, Rezervacija.kraj).where(
            Rezervacija.pocetak >= date_value.replace(hour=0, minute=0, second=0, microsecond=0),
            Rezervacija.kraj <= date_value.replace(hour=23, minute=59, second=59, microsecond=999999),
        )
    )
    reservations = [
        {"pocetak": row[0], "kraj": row[1]}
        for row in reservations_result.all()
    ]

    slots = build_available_starts(radno_vrijeme, reservations)

    return {
        "radno_vrijeme": radno_vrijeme,
        "slobodni_pocetci": slots,
        "usluge": await get_usluge_async(session),
    }


@app.get("/api/rezervacije/moje")
async def list_moje_rezervacije(
    session: AsyncSession = Depends(get_async_session),
    current_user: dict = Depends(get_current_user),
) -> list[dict]:
    result = await session.execute(
        select(Rezervacija, Usluga.naziv.label("usluga_naziv"), Usluga.cijena)
        .join(Usluga, Usluga.id == Rezervacija.usluga_id)
        .where(Rezervacija.klijent_id == current_user["id"])
        .order_by(Rezervacija.pocetak.desc())
    )

    now = datetime.now(timezone.utc)
    rows: list[dict] = []
    for reservation, usluga_naziv, cijena in result.all():
        status_name = await session.scalar(
            select(StatusRezervacija.naziv).where(StatusRezervacija.id == reservation.status_id)
        )
        review_exists = await session.scalar(
            select(Recenzija.id).where(Recenzija.rezervacija_id == reservation.id)
        )
        rows.append({
            "id": reservation.id,
            "usluga_naziv": usluga_naziv,
            "cijena": cijena,
            "pocetak": reservation.pocetak,
            "kraj": reservation.kraj,
            "status": status_name,
            "biljeska": reservation.biljeska,
            "can_cancel": can_cancel_reservation(reservation.pocetak, reservation.status_id, now),
            "can_review": can_review_reservation(reservation.kraj, review_exists is not None, now),
        })

    return rows


@app.get("/api/rezervacije/admin-pregled")
async def admin_pregled_rezervacija(
    datum: str,
    session: AsyncSession = Depends(get_async_session),
    current_user: dict = Depends(require_admin),
) -> list[dict]:
    try:
        date_value = datetime.fromisoformat(datum)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_date") from exc

    start_of_day = date_value.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + timedelta(days=1)

    result = await session.execute(
        select(
            Rezervacija,
            Usluga.naziv.label("usluga_naziv"),
            StatusRezervacija.naziv.label("status_naziv"),
            Korisnik.ime,
            Korisnik.prezime,
            Korisnik.broj_mobitela,
        )
        .join(Usluga, Usluga.id == Rezervacija.usluga_id)
        .join(Korisnik, Korisnik.id == Rezervacija.klijent_id)
        .join(StatusRezervacija, StatusRezervacija.id == Rezervacija.status_id)
        .where(
            Rezervacija.pocetak >= start_of_day,
            Rezervacija.pocetak < end_of_day,
        )
        .order_by(Rezervacija.pocetak.asc())
    )

    rows: list[dict] = []
    for reservation, usluga_naziv, status_naziv, ime, prezime, broj_mobitela in result.all():
        rows.append({
            "id": reservation.id,
            "pocetak": reservation.pocetak,
            "kraj": reservation.kraj,
            "usluga_naziv": usluga_naziv,
            "status": status_naziv,
            "biljeska": reservation.biljeska,
            "klijent": {
                "id": reservation.klijent_id,
                "ime": ime,
                "prezime": prezime,
                "broj_mobitela": broj_mobitela,
            },
        })
    return rows


@app.get("/api/rezervacije/{rezervacija_id}", response_model=models.RezervacijaOut)
async def get_rezervacija(
    rezervacija_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: dict = Depends(get_current_user),
) -> dict:
    row = await get_rezervacija_by_id_async(session, rezervacija_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="rezervacija_not_found")
    if not can_access_reservation(current_user, row):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
    return row


@app.patch("/api/rezervacije/{rezervacija_id}/status")
async def update_rezervacija_status(
    rezervacija_id: int,
    payload: dict,
    session: AsyncSession = Depends(get_async_session),
    current_user: dict = Depends(get_current_user),
) -> dict:
    if "status_id" not in payload:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_status")

    try:
        new_status_id = int(payload["status_id"])
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_status") from exc

    if new_status_id not in {1, 2, 3}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_status")

    reservation = await get_rezervacija_by_id_async(session, rezervacija_id)
    if reservation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="rezervacija_not_found")

    if not can_access_reservation(current_user, reservation):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")

    if not is_admin_user(current_user) and new_status_id != 3:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")

    if not is_admin_user(current_user) and reservation["klijent_id"] != current_user["id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")

    if new_status_id == 3 and not can_cancel_reservation(
        datetime.fromisoformat(str(reservation["pocetak"])),
        reservation["status_id"],
        datetime.now(timezone.utc),
    ):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="reservation_cannot_be_cancelled")

    result = await session.execute(select(Rezervacija.id).where(Rezervacija.id == rezervacija_id))
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="rezervacija_not_found")

    await session.execute(
        update(Rezervacija)
        .where(Rezervacija.id == rezervacija_id)
        .values(status_id=new_status_id)
    )
    await session.commit()

    return {
        "status": "success",
        "poruka": "Status rezervacije uspješno ažuriran.",
    }


@app.post("/api/korisnici/klijent", response_model=models.KlijentCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_klijent(
    payload: models.KlijentCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user: dict = Depends(require_admin),
) -> dict:
    if await get_korisnik_by_email_async(session, str(payload.email or "")) if payload.email else False:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="email_already_registered")

    created = await create_klijent_async(
        session,
        ime=payload.ime,
        prezime=payload.prezime,
        broj_mobitela=payload.broj_mobitela,
        email=str(payload.email) if payload.email else None,
    )
    return {
        "status": "success",
        "klijent_id": created["id"],
        "poruka": "Brzi profil klijenta uspješno kreiran.",
    }


@app.patch("/api/korisnici/{korisnik_id}/rola")
async def update_korisnik_rola(
    korisnik_id: int,
    payload: models.UserRoleUpdate,
    session: AsyncSession = Depends(get_async_session),
    current_user: dict = Depends(require_admin),
) -> dict:
    try:
        updated = await update_korisnik_rola_async(session, korisnik_id, payload.rola_id)
    except ValueError as exc:
        if str(exc) == "korisnik_not_found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="korisnik_not_found") from exc
        raise

    return {
        "status": "success",
        "poruka": "Korisnička uloga uspješno promijenjena.",
        "user_id": updated["id"],
        "rola_id": updated["rola_id"],
    }


@app.post("/api/rezervacije", response_model=models.RezervacijaCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_rezervacija(
    payload: models.RezervacijaCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user: dict = Depends(get_current_user),
) -> dict:
    if payload.kraj <= payload.pocetak:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_time_range")

    if not is_admin_user(current_user) and payload.klijent_id != current_user["id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")

    usluga_exists = await session.execute(select(Usluga.id).where(Usluga.id == payload.usluga_id))
    if usluga_exists.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="usluga_not_found")

    klijent = await get_korisnik_by_id_async(session, payload.klijent_id)
    if klijent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="klijent_not_found")

    overlaps = await has_overlapping_rezervacija_async(session, payload.pocetak, payload.kraj)
    if overlaps:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="timeslot_unavailable")

    created = await create_rezervacija_async(
        session,
        pocetak=payload.pocetak,
        kraj=payload.kraj,
        usluga_id=payload.usluga_id,
        klijent_id=payload.klijent_id,
        biljeska=payload.biljeska,
    )
    return {
        "status": "success",
        "rezervacija_id": created["id"],
        "poruka": "Rezervacija uspješno kreirana.",
    }


@app.post("/api/biljeske", status_code=status.HTTP_201_CREATED)
async def create_biljeska(
    payload: dict,
    session: AsyncSession = Depends(get_async_session),
    current_user: dict = Depends(require_admin),
) -> dict:
    if "rezervacija_id" not in payload or "text" not in payload:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_payload")

    rezervacija_id = payload["rezervacija_id"]
    text_value = str(payload["text"]).strip()
    if not text_value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_payload")

    reservation = await get_rezervacija_by_id_async(session, int(rezervacija_id))
    if reservation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="rezervacija_not_found")

    existing_note = await session.scalar(
        select(KlijentBiljeska.id).where(KlijentBiljeska.rezervacija_id == int(rezervacija_id))
    )
    if existing_note is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="note_already_exists")

    session.add(KlijentBiljeska(text=text_value, rezervacija_id=int(rezervacija_id)))
    await session.commit()

    return {
        "status": "success",
        "poruka": "Administrativna bilješka spremljena.",
    }


@app.get("/api/recenzije/usluga/{usluga_id}", response_model=list[models.RecenzijaOut])
async def list_recenzije_for_usluga(
    usluga_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: dict = Depends(get_current_user),
) -> list[dict]:
    return await list_recenzije_for_usluga_async(session, usluga_id)


@app.post("/api/recenzije", response_model=models.RecenzijaCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_recenzija(
    payload: models.RecenzijaCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user: dict = Depends(get_current_user),
) -> dict:
    if not is_admin_user(current_user) and payload.klijent_id != current_user["id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")

    rezervacija_exists = await session.execute(select(Rezervacija.id).where(Rezervacija.id == payload.rezervacija_id))
    if rezervacija_exists.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="rezervacija_not_found")

    usluga_exists = await session.execute(select(Usluga.id).where(Usluga.id == payload.usluga_id))
    if usluga_exists.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="usluga_not_found")

    klijent_exists = await session.execute(select(Korisnik.id).where(Korisnik.id == payload.klijent_id))
    if klijent_exists.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="klijent_not_found")

    created = await create_recenzija_async(
        session,
        ocjena=payload.ocjena,
        rezervacija_id=payload.rezervacija_id,
        usluga_id=payload.usluga_id,
        klijent_id=payload.klijent_id,
        komentar=payload.komentar,
    )
    return {
        "status": "success",
        "recenzija_id": created["id"],
        "poruka": "Recenzija uspješno kreirana.",
    }
