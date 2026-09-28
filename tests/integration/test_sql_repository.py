from datetime import datetime, timedelta, timezone

import pytest

from app.models.event import EventStatus
from app.repositories.event_record import EventRecord

pytestmark = pytest.mark.integration


def make_record(**overrides) -> EventRecord:
    defaults = {
        "id": None,
        "venue_id": 1,
        "title": "Launch",
        "description": None,
        "starts_at": datetime(2026, 9, 1, 18, 0),
        "ends_at": datetime(2026, 9, 1, 21, 0),
        "status": EventStatus.draft,
        "created_by": 1,
    }
    defaults.update(overrides)
    return EventRecord(**defaults)


# tests/integration/test_admin_events_routes.py


# ---------------------------------------------------------------------------
# POST /admin/events  (create_event)
# ---------------------------------------------------------------------------


async def test_create_event_success(auth_client, make_venue):
    venue = await make_venue()
    starts_at = datetime.now(timezone.utc) + timedelta(days=10)
    ends_at = starts_at + timedelta(hours=2)

    payload = {
        "venue_id": venue.id,
        "title": "Tech Conference 2026",
        "description": "A great conference",
        "starts_at": starts_at.isoformat(),
        "ends_at": ends_at.isoformat(),
    }

    res = await auth_client.post("/admin/events", json=payload)

    assert res.status_code == 201
    body = res.json()
    assert body["title"] == "Tech Conference 2026"
    assert body["venue_id"] == venue.id
    assert "id" in body


async def test_create_event_invalid_times_returns_400(auth_client, make_venue):
    venue = await make_venue()
    starts_at = datetime.now(timezone.utc) + timedelta(days=10)
    ends_at = starts_at - timedelta(hours=1)  # ends before it starts

    payload = {
        "venue_id": venue.id,
        "title": "Broken Event",
        "description": "Bad times",
        "starts_at": starts_at.isoformat(),
        "ends_at": ends_at.isoformat(),
    }

    res = await auth_client.post("/admin/events", json=payload)

    assert res.status_code == 422


async def test_create_event_nonexistent_venue_returns_404(auth_client):
    starts_at = datetime.now(timezone.utc) + timedelta(days=10)
    ends_at = starts_at + timedelta(hours=2)

    payload = {
        "venue_id": 999_999,
        "title": "Ghost Venue Event",
        "description": "No venue",
        "starts_at": starts_at.isoformat(),
        "ends_at": ends_at.isoformat(),
    }

    res = await auth_client.post("/admin/events", json=payload)

    assert res.status_code == 404


async def test_create_event_missing_required_field_returns_422(auth_client, make_venue):
    venue = await make_venue()

    payload = {
        "venue_id": venue.id,
        # "title" intentionally omitted
        "starts_at": datetime.now(timezone.utc).isoformat(),
        "ends_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
    }

    res = await auth_client.post("/admin/events", json=payload)

    assert res.status_code == 422


async def test_create_event_requires_admin(customer, make_venue):
    venue = await make_venue()
    payload = {
        "venue_id": venue.id,
        "title": "Unauthorized attempt",
        "starts_at": datetime.now(timezone.utc).isoformat(),
        "ends_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
    }

    res = await customer.post("/admin/events", json=payload)

    assert res.status_code == 401


# ---------------------------------------------------------------------------
# GET /admin/events/{event_id}  (get_event)
# ---------------------------------------------------------------------------


async def test_get_event_success(auth_client, make_event):
    event = await make_event()

    res = await auth_client.get(f"/admin/events/{event.id}")

    assert res.status_code == 200
    body = res.json()
    assert body["id"] == event.id
    assert body["title"] == event.title


async def test_get_event_not_found_returns_404(auth_client):
    res = await auth_client.get("/admin/events/999999")

    assert res.status_code == 404


async def test_get_event_requires_admin(customer, make_event):
    event = await make_event()

    res = await customer.get(f"/admin/events/{event.id}")

    assert res.status_code == 401


# ---------------------------------------------------------------------------
# GET /admin/events  (list_events)
# ---------------------------------------------------------------------------


async def test_list_events_success(auth_client, make_event):
    await make_event()
    await make_event()
    await make_event()

    res = await auth_client.get("/admin/events")

    assert res.status_code == 200
    body = res.json()
    assert "results" in body
    assert body["total_items"] >= 3
    assert len(body["results"]) <= 10  # default page_size


async def test_list_events_pagination(auth_client, make_event):
    for _ in range(15):
        await make_event()

    res = await auth_client.get("/admin/events", params={"page": 1, "page_size": 5})

    assert res.status_code == 200
    body = res.json()
    print(body)
    assert len(body["results"]) == 5


async def test_list_events_invalid_page_returns_422(auth_client):
    res = await auth_client.get("/admin/events", params={"page": 0})

    assert res.status_code == 422


# async def test_list_events_page_size_too_large_returns_422(auth_client):
#     res = await auth_client.get("/admin/events", params={"page_size": 500})

#     assert res.status_code == 422


async def test_list_events_requires_admin(customer):
    res = await customer.get("/admin/events")

    assert res.status_code == 401


# # ---------------------------------------------------------------------------
# # PATCH /admin/events/{event_id}  (update_event)
# # ---------------------------------------------------------------------------


# async def test_update_event_success(auth_client, make_event):
#     event = await make_event(title="Original Title")

#     res = await auth_client.patch(
#         f"/admin/events/{event.id}",
#         json={"title": "Updated Title"},
#     )

#     assert res.status_code == 202
#     body = res.json()
#     assert body["title"] == "Updated Title"


# async def test_update_event_not_found_returns_404(auth_client):
#     res = await auth_client.patch(
#         "/admin/events/999999",
#         json={"title": "Doesn't matter"},
#     )

#     assert res.status_code == 404


# async def test_update_event_invalid_times_returns_400(auth_client, make_event):
#     event = await make_event()
#     bad_ends_at = event.starts_at - timedelta(hours=1)

#     res = await auth_client.patch(
#         f"/admin/events/{event.id}",
#         json={"ends_at": bad_ends_at.isoformat()},
#     )

#     assert res.status_code == 400


# async def test_update_event_requires_admin(client, make_event):
#     event = await make_event()

#     res = await client.patch(
#         f"/admin/events/{event.id}",
#         json={"title": "Hacked Title"},
#     )

#     assert res.status_code == 401


# # ---------------------------------------------------------------------------
# # PATCH /admin/events/{event_id}/status  (change_event_status)
# # ---------------------------------------------------------------------------


# async def test_change_event_status_success(auth_client, make_event):
#     event = await make_event()  # defaults to draft

#     res = await auth_client.patch(
#         f"/admin/events/{event.id}/status",
#         params={"new_status": "published"},
#     )

#     assert res.status_code == 200
#     body = res.json()
#     assert body["status"] == "published"


# async def test_change_event_status_invalid_transition_returns_400(
#     auth_client, make_event
# ):
#     from app.models import EventStatus

#     event = await make_event(status=EventStatus.cancelled)

#     res = await auth_client.patch(
#         f"/admin/events/{event.id}/status",
#         params={"new_status": "published"},
#     )

#     assert res.status_code == 400


# async def test_change_event_status_not_found_returns_404(auth_client):
#     res = await auth_client.patch(
#         "/admin/events/999999/status",
#         params={"new_status": "published"},
#     )

#     assert res.status_code == 404


# async def test_change_event_status_invalid_value_returns_400_or_422(
#     auth_client, make_event
# ):
#     event = await make_event()

#     res = await auth_client.patch(
#         f"/admin/events/{event.id}/status",
#         params={"new_status": "not_a_real_status"},
#     )

#     assert res.status_code in (400, 422)


# async def test_change_event_status_requires_admin(client, make_event):
#     event = await make_event()

#     res = await client.patch(
#         f"/admin/events/{event.id}/status",
#         params={"new_status": "published"},
#     )

#     assert res.status_code == 401


# # ---------------------------------------------------------------------------
# # DELETE /admin/events/{event_id}  (delete_event)
# # ---------------------------------------------------------------------------


# async def test_delete_event_success(auth_client, make_event):
#     from app.models import EventStatus

#     event = await make_event(status=EventStatus.draft)

#     res = await auth_client.delete(f"/admin/events/{event.id}")

#     assert res.status_code == 204

#     # verify it's actually gone
#     follow_up = await auth_client.get(f"/admin/events/{event.id}")
#     assert follow_up.status_code == 404


# async def test_delete_published_event_returns_400(auth_client, make_event):
#     from app.models import EventStatus

#     event = await make_event(status=EventStatus.published)

#     res = await auth_client.delete(f"/admin/events/{event.id}")

#     assert res.status_code == 400


# async def test_delete_event_not_found_returns_404(auth_client):
#     res = await auth_client.delete("/admin/events/999999")

#     assert res.status_code == 404


# async def test_delete_event_requires_admin(client, make_event):
#     event = await make_event()

#     res = await client.delete(f"/admin/events/{event.id}")

#     assert res.status_code == 401
