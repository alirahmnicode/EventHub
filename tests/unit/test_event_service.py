from datetime import timedelta

import pytest
from pydantic import ValidationError

from app.core.exceptions import (
    NotFoundError,
    PermissionDeniedError,
)
from app.models.enums import EventStatus, UserRole
from app.models.event import Event
from app.repositories.event import EventRepository
from app.services.event import MAX_PAGE_SIZE, EventService
from tests.unit.conftest import ENDS_AT, STARTS_AT


@pytest.fixture
def event(make_event):
    return make_event(
        id=1, status=EventStatus.PUBLISHED, starts_at=STARTS_AT, ends_at=ENDS_AT
    )


@pytest.fixture
def repo(make_repo, event):
    repo = make_repo(EventRepository)
    repo.get.return_value = event
    repo.get_list.return_value = [event]
    return repo


@pytest.fixture
def service(repo) -> EventService:
    return EventService(repo)


# ---------- get_event ----------


@pytest.mark.parametrize("status", [EventStatus.PUBLISHED, EventStatus.CANCELLED])
@pytest.mark.parametrize("role", [None, UserRole.CUSTOMER, UserRole.ADMIN])
async def test_get_public_event_visible_to_everyone(
    service, repo, make_event, make_user, status, role
):
    event = make_event(status=status)
    repo.get.return_value = event
    user = make_user(role=role) if role else None

    assert await service.get_event(1, user) is event


@pytest.mark.parametrize("role", [None, UserRole.CUSTOMER])
async def test_get_draft_event_denied_for_non_admin(
    service, repo, make_event, make_user, role
):
    repo.get.return_value = make_event(status=EventStatus.DRAFT)
    user = make_user(role=role) if role else None

    with pytest.raises(PermissionDeniedError):
        await service.get_event(1, user)


async def test_get_draft_event_allowed_for_admin(service, repo, make_event, admin):
    draft = make_event(status=EventStatus.DRAFT)
    repo.get.return_value = draft

    assert await service.get_event(1, admin) is draft


async def test_get_event_not_found(service, repo):
    repo.get.return_value = None

    with pytest.raises(NotFoundError):
        await service.get_event(999)


# ---------- list_events ----------


async def test_list_hides_drafts_from_anonymous(service, repo):
    await service.list_events()

    filters = repo.get_list.await_args.kwargs["filters"]
    assert len(filters) == 1
    assert filters[0].compare(Event.status != EventStatus.DRAFT)


async def test_list_hides_drafts_from_customer(service, repo, regular_user):
    await service.list_events(user=regular_user)

    filters = repo.get_list.await_args.kwargs["filters"]
    assert len(filters) == 1
    assert filters[0].compare(Event.status != EventStatus.DRAFT)


async def test_list_shows_drafts_to_admin(service, repo, admin):
    await service.list_events(user=admin)

    assert list(repo.get_list.await_args.kwargs["filters"]) == []


async def test_list_adds_venue_and_search_filters(service, repo, admin):
    await service.list_events(user=admin, venue_id=5, search="rock")

    filters = repo.get_list.await_args.kwargs["filters"]
    assert len(filters) == 2
    assert filters[0].compare(Event.venue_id == 5)
    assert filters[1].compare(Event.title.ilike("%rock%"))


async def test_list_orders_newest_first(service, repo):
    await service.list_events()

    order_by = repo.get_list.await_args.kwargs["order_by"]
    assert len(order_by) == 1
    assert order_by[0].compare(Event.id.desc())


async def test_list_returns_repo_result(service, repo, event):
    assert await service.list_events() == [event]


@pytest.mark.parametrize(
    "offset, limit, expected_offset, expected_limit",
    [
        (-5, 20, 0, 20),
        (0, 0, 0, 1),
        (0, 10_000, 0, MAX_PAGE_SIZE),
        (40, 10, 40, 10),
    ],
)
async def test_list_clamps_pagination(
    service, repo, offset, limit, expected_offset, expected_limit
):
    await service.list_events(offset=offset, limit=limit)

    kwargs = repo.get_list.await_args.kwargs
    assert kwargs["offset"] == expected_offset
    assert kwargs["limit"] == expected_limit


# ---------- create_event ----------


async def test_create_allowed_for_admin(
    service, repo, admin, make_event, make_event_create
):
    data = make_event_create()
    created = make_event(id=100)
    repo.create.return_value = created

    result = await service.create_event(data, admin)

    assert result is created
    repo.create.assert_awaited_once_with(data, created_by=admin.id)


async def test_create_forbidden_for_non_admin(
    service, repo, regular_user, make_event_create
):
    with pytest.raises(PermissionDeniedError):
        await service.create_event(make_event_create(), regular_user)

    repo.create.assert_not_awaited()


@pytest.mark.parametrize(
    "starts_at, ends_at",
    [
        (ENDS_AT, STARTS_AT),  # starts after it ends
        (STARTS_AT, STARTS_AT),  # zero duration
        (STARTS_AT, STARTS_AT - timedelta(seconds=1)),
    ],
)
def test_create_invalid_date_range(make_event_create, starts_at, ends_at):
    with pytest.raises(ValidationError):
        make_event_create(starts_at=starts_at, ends_at=ends_at)


async def test_create_checks_permission_before_validation(
    service, regular_user, make_event_create
):
    with pytest.raises(PermissionDeniedError):
        data = make_event_create()
        await service.create_event(data, regular_user)


# ---------- update_event ----------


async def test_update_allowed_for_admin(service, repo, admin, event, make_event_update):
    data = make_event_update(starts_at=STARTS_AT, ends_at=ENDS_AT)
    repo.update.return_value = event

    result = await service.update_event(1, data, admin)

    assert result is event
    repo.update.assert_awaited_once_with(event, data)


async def test_update_forbidden_for_non_admin(
    service, repo, regular_user, make_event_update
):
    data = make_event_update(starts_at=STARTS_AT, ends_at=ENDS_AT)

    with pytest.raises(PermissionDeniedError):
        await service.update_event(1, data, regular_user)

    repo.update.assert_not_awaited()


async def test_update_not_found(service, repo, admin, make_event_update):
    repo.get.return_value = None
    data = make_event_update(starts_at=STARTS_AT, ends_at=ENDS_AT)

    with pytest.raises(NotFoundError):
        await service.update_event(999, data, admin)

    repo.update.assert_not_awaited()


async def test_update_invalid_date_range(service, repo, admin, make_event_update):

    with pytest.raises(ValidationError):
        data = make_event_update(starts_at=ENDS_AT, ends_at=STARTS_AT)
        await service.update_event(1, data, admin)

    repo.update.assert_not_awaited()


async def test_update_without_dates_is_allowed(
    service, repo, admin, event, make_event_update
):
    data = make_event_update(
        title="Only the title changes", starts_at=None, ends_at=None
    )
    repo.update.return_value = event

    await service.update_event(1, data, admin)

    repo.update.assert_awaited_once_with(event, data)


# ---------- delete_event ----------


async def test_delete_allowed_for_admin(service, repo, admin, event):
    await service.delete_event(1, admin)

    repo.delete.assert_awaited_once_with(event)


async def test_delete_forbidden_for_non_admin(service, repo, regular_user):
    with pytest.raises(PermissionDeniedError):
        await service.delete_event(1, regular_user)

    repo.delete.assert_not_awaited()


async def test_delete_not_found(service, repo, admin):
    repo.get.return_value = None

    with pytest.raises(NotFoundError):
        await service.delete_event(999, admin)

    repo.delete.assert_not_awaited()
