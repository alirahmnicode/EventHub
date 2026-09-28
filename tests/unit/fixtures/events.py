from datetime import datetime

import pytest

from app.models.enums import EventStatus
from app.repositories.event_record import EventRecord
from app.repositories.venue_record import VenueRecord
from app.services.event import (
    EventService,
)

from .fakes import FakeEventRepository, FakeVenueLookup


def make_record(**overrides) -> EventRecord:
    defaults = {
        "id": 1,
        "venue_id": 10,
        "title": "Launch",
        "description": None,
        "starts_at": datetime(2026, 9, 1, 18, 0),
        "ends_at": datetime(2026, 9, 1, 21, 0),
        "status": EventStatus.draft,
        "created_by": 5,
    }
    defaults.update(overrides)
    return EventRecord(**defaults)


def make_service(events=None, venues=None) -> EventService:
    """venues defaults to a single venue with id=10, matching make_record's
    default venue_id, so existing tests don't all need updating."""
    if venues is None:
        venues = [VenueRecord(id=10, name="Test Venue")]
    return EventService(FakeEventRepository(events), FakeVenueLookup(venues))


@pytest.fixture(scope="package")
def get_event_service():
    def create_events(events=None, venues=None):
        if events is None:
            events = [make_record()]

        if venues is None:
            venues = [VenueRecord(id=10, name="Test Venue")]

        service = make_service(events=events)
        return service

    return create_events
