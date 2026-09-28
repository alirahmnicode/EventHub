from datetime import datetime

import pytest
from fastapi.exceptions import RequestValidationError

from app.models.enums import EventStatus
from app.repositories.interfaces import NotFoundError
from app.schemas.event import EventCreateSchema, EventUpdateSchema
from app.services.event import (
    CannotDeletePublishedEventError,
    EventService,
    InvalidEventTimesError,
    InvalidStatusTransitionError,
)

from .fixtures.events import get_event_service, make_record

# --- test get event -----------------------------------------------------------------


@pytest.mark.unit
async def test_get_event_by_id(get_event_service: EventService):
    service = get_event_service()
    event = await service.get_event(event_id=1)

    assert event.id == 1


@pytest.mark.unit
async def test_not_found_event(get_event_service: EventService):
    service = get_event_service()
    with pytest.raises(NotFoundError) as exc_info:
        await service.get_event(event_id=1000)


@pytest.mark.unit
async def test_get_all_events(get_event_service: EventService):
    events = [make_record(id=i) for i in range(1, 21)]
    service = get_event_service(events=events)

    events_list, total = await service.list_events(page=1, page_size=20)

    assert len(events_list) == 20
    assert total == 20


# --- test create event --------------------------------------------------------------


@pytest.mark.unit
async def test_create_event_rejects_missing_venue(get_event_service: EventService):
    service = get_event_service(venues=[])
    data = EventCreateSchema(
        venue_id=999,
        title="Launch",
        starts_at=datetime(2026, 9, 1, 18, 0),
        ends_at=datetime(2026, 9, 1, 21, 0),
    )
    with pytest.raises(NotFoundError) as exc_info:
        await service.create_event(data, created_by=5)

    assert exc_info.value.resource == "Venue"
    assert exc_info.value.resource_id == 999


@pytest.mark.unit
async def test_create_event_rejects_ends_before_starts(get_event_service: EventService):
    service = get_event_service()
    with pytest.raises(RequestValidationError):
        bad = EventCreateSchema(
            venue_id=10,
            title="Bad",
            starts_at=datetime(2026, 9, 1, 21, 0),
            ends_at=datetime(2026, 9, 1, 18, 0),
            status=EventStatus.draft,
        )

        await service.create_event(bad, created_by=5)


@pytest.mark.unit
async def test_create_event_starts_as_draft(get_event_service: EventService):
    service = get_event_service()
    data = EventCreateSchema(
        venue_id=10,
        title="Launch",
        starts_at=datetime(2026, 9, 1, 18, 0),
        ends_at=datetime(2026, 9, 1, 21, 0),
    )
    created = await service.create_event(data, created_by=5)
    assert created.status == EventStatus.draft


# --- test update event ----------------------------------------------------------------------
@pytest.mark.unit
async def test_update_event_partial_change_keeps_other_fields(
    get_event_service: EventService,
):
    service = get_event_service()

    updated = await service.update_event(1, EventUpdateSchema(title="New Title"))

    assert updated.title == "New Title"
    assert updated.venue_id == 10  # untouched


@pytest.mark.unit
async def test_update_event_rejects_bad_times(
    get_event_service: EventService,
):
    service = get_event_service()

    with pytest.raises(InvalidEventTimesError):
        await service.update_event(
            1,
            EventUpdateSchema(
                starts_at=datetime(2026, 9, 1, 22, 0),
                ends_at=datetime(2026, 9, 1, 20, 0),
            ),
        )


# ---- test publish event ---------------------------------------------------------------------------------


@pytest.mark.unit
async def test_publish_draft_event_succeeds(
    get_event_service: EventService,
):
    service = get_event_service(events=[make_record(status=EventStatus.draft)])

    updated = await service.change_status(1, EventStatus.published)
    assert updated.status == EventStatus.published


@pytest.mark.unit
async def test_cannot_publish_a_cancelled_event(
    get_event_service: EventService,
):
    service = get_event_service(events=[make_record(status=EventStatus.cancelled)])

    with pytest.raises(InvalidStatusTransitionError):
        await service.change_status(1, EventStatus.published)


@pytest.mark.unit
async def test_cannot_revert_published_event_to_draft(
    get_event_service: EventService,
):
    service = get_event_service(events=[make_record(status=EventStatus.published)])

    with pytest.raises(InvalidStatusTransitionError):
        await service.change_status(1, EventStatus.draft)


# --- test delete event ----------------------------------------------------------------------------


@pytest.mark.unit
async def test_cannot_delete_published_event(
    get_event_service: EventService,
):
    service = get_event_service(events=[make_record(status=EventStatus.published)])

    with pytest.raises(CannotDeletePublishedEventError):
        await service.delete_event(1)


@pytest.mark.unit
async def test_can_delete_draft_event(
    get_event_service: EventService,
):
    service = get_event_service(events=[make_record(status=EventStatus.draft)])

    await service.delete_event(1)
    with pytest.raises(NotFoundError):
        await service.get_event(1)
