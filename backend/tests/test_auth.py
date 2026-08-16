from datetime import datetime, timezone

import pytest
from fastapi import HTTPException

from app.main import (
    build_available_starts,
    can_access_reservation,
    can_cancel_reservation,
    can_review_reservation,
    is_admin_user,
)
from app.security import get_current_user, require_admin


@pytest.mark.asyncio
async def test_get_current_user_requires_token():
    with pytest.raises(HTTPException) as exc:
        await get_current_user(None)

    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_require_admin_rejects_customer():
    with pytest.raises(HTTPException) as exc:
        await require_admin({"rola_id": 2})

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_require_admin_allows_admin():
    result = await require_admin({"rola_id": 1})
    assert result["rola_id"] == 1


def test_build_available_starts_ignores_reserved_slots():
    shift_start = datetime(2026, 8, 25, 9, 0, tzinfo=timezone.utc)
    shift_end = datetime(2026, 8, 25, 10, 0, tzinfo=timezone.utc)
    reservations = [
        {
            "pocetak": datetime(2026, 8, 25, 9, 15, tzinfo=timezone.utc),
            "kraj": datetime(2026, 8, 25, 9, 45, tzinfo=timezone.utc),
        }
    ]

    starts = build_available_starts([shift_start, shift_end], reservations)

    assert starts == [
        "2026-08-25T09:00:00+00:00",
        "2026-08-25T09:45:00+00:00",
    ]


def test_is_admin_user_and_owner_checks():
    assert is_admin_user({"rola_id": 1}) is True
    assert is_admin_user({"rola_id": 2}) is False
    assert can_access_reservation({"id": 7, "rola_id": 2}, {"klijent_id": 7}) is True
    assert can_access_reservation({"id": 7, "rola_id": 2}, {"klijent_id": 8}) is False
    assert can_access_reservation({"id": 7, "rola_id": 1}, {"klijent_id": 8}) is True


def test_reservation_action_flags_match_spec_logic():
    now = datetime(2026, 8, 25, 12, 0, tzinfo=timezone.utc)

    assert can_cancel_reservation(
        datetime(2026, 8, 25, 13, 0, tzinfo=timezone.utc),
        status_id=2,
        now=now,
    ) is True
    assert can_cancel_reservation(
        datetime(2026, 8, 25, 11, 0, tzinfo=timezone.utc),
        status_id=2,
        now=now,
    ) is False
    assert can_cancel_reservation(
        datetime(2026, 8, 25, 13, 0, tzinfo=timezone.utc),
        status_id=3,
        now=now,
    ) is False

    assert can_review_reservation(
        datetime(2026, 8, 25, 11, 0, tzinfo=timezone.utc),
        has_review=False,
        now=now,
    ) is True
    assert can_review_reservation(
        datetime(2026, 8, 25, 13, 0, tzinfo=timezone.utc),
        has_review=False,
        now=now,
    ) is False
    assert can_review_reservation(
        datetime(2026, 8, 25, 11, 0, tzinfo=timezone.utc),
        has_review=True,
        now=now,
    ) is False
