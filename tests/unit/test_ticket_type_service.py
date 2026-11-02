from datetime import timedelta

import pytest
from pydantic import ValidationError

from app.core.exceptions import (
    ConflictError,
    DomainValidationError,
    NotFoundError,
    PermissionDeniedError,
)
from app.models.enums import EventStatus, UserRole
from app.models.ticket_type import TicketType
from app.repositories import EventRepository, TicketTypeRepository
from app.services.ticket_type import MAX_PAGE_SIZE, TicketTypeService
from tests.unit.conftest import SALES_END, SALES_START

# ---------- local fixtures ----------


@pytest.fixture
def ticket_type(make_ticket_type):
    # committed stock = 10 reserved + 20 sold = 30
    return make_ticket_type(id=1, reserved_quantity=10, sold_quantity=20)


@pytest.fixture
def event(make_event):
    return make_event(id=1, status=EventStatus.PUBLISHED)


@pytest.fixture
def repo(make_repo, ticket_type):
    repo = make_repo(TicketTypeRepository)
    repo.get.return_value = ticket_type
    repo.get_list.return_value = [ticket_type]
    return repo


@pytest.fixture
def event_repo(make_repo, event):
    event_repo = make_repo(EventRepository)
    event_repo.get.return_value = event
    return event_repo


@pytest.fixture
def service(repo, event_repo) -> TicketTypeService:
    return TicketTypeService(repo, event_repo)


# ---------- get_ticket_type ----------


@pytest.mark.parametrize("status", [EventStatus.PUBLISHED, EventStatus.CANCELLED])
@pytest.mark.parametrize("role", [None, UserRole.CUSTOMER, UserRole.ADMIN])
async def test_get_visible_for_public_event(
    service, event_repo, make_event, make_user, ticket_type, status, role
):
    event_repo.get.return_value = make_event(status=status)
    user = make_user(role=role) if role else None

    assert await service.get_ticket_type(1, user) is ticket_type


@pytest.mark.parametrize("role", [None, UserRole.CUSTOMER])
async def test_get_denied_for_draft_event_non_admin(
    service, event_repo, make_event, make_user, role
):
    event_repo.get.return_value = make_event(status=EventStatus.DRAFT)
    user = make_user(role=role) if role else None

    with pytest.raises(PermissionDeniedError):
        await service.get_ticket_type(1, user)


async def test_get_allowed_for_draft_event_admin(
    service, event_repo, make_event, admin, ticket_type
):
    event_repo.get.return_value = make_event(status=EventStatus.DRAFT)

    assert await service.get_ticket_type(1, admin) is ticket_type


async def test_get_loads_the_ticket_types_own_event(service, event_repo, ticket_type):
    await service.get_ticket_type(1)

    event_repo.get.assert_awaited_once_with(ticket_type.event_id)


async def test_get_ticket_type_not_found(service, repo, event_repo):
    repo.get.return_value = None

    with pytest.raises(NotFoundError):
        await service.get_ticket_type(999)

    event_repo.get.assert_not_awaited()


async def test_get_event_not_found(service, event_repo):
    event_repo.get.return_value = None

    with pytest.raises(NotFoundError):
        await service.get_ticket_type(1)


# ---------- list_ticket_types ----------


async def test_list_returns_repo_result(service, ticket_type):
    assert await service.list_ticket_types(1) == [ticket_type]


async def test_list_filters_by_event_and_orders_by_price(service, repo):
    await service.list_ticket_types(5)

    kwargs = repo.get_list.await_args.kwargs
    assert len(kwargs["filters"]) == 1
    assert kwargs["filters"][0].compare(TicketType.event_id == 5)

    order_by = kwargs["order_by"]
    assert len(order_by) == 2
    assert order_by[0].compare(TicketType.price_cents.asc())
    assert order_by[1].compare(TicketType.id.asc())


async def test_list_event_not_found(service, repo, event_repo):
    event_repo.get.return_value = None

    with pytest.raises(NotFoundError):
        await service.list_ticket_types(999)

    repo.get_list.assert_not_awaited()


@pytest.mark.parametrize("role", [None, UserRole.CUSTOMER])
async def test_list_denied_for_draft_event_non_admin(
    service, repo, event_repo, make_event, make_user, role
):
    event_repo.get.return_value = make_event(status=EventStatus.DRAFT)
    user = make_user(role=role) if role else None

    with pytest.raises(PermissionDeniedError):
        await service.list_ticket_types(1, user=user)

    repo.get_list.assert_not_awaited()


async def test_list_allowed_for_draft_event_admin(
    service, repo, event_repo, make_event, admin
):
    event_repo.get.return_value = make_event(status=EventStatus.DRAFT)

    await service.list_ticket_types(1, user=admin)

    repo.get_list.assert_awaited_once()


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
    await service.list_ticket_types(1, offset=offset, limit=limit)

    kwargs = repo.get_list.await_args.kwargs
    assert kwargs["offset"] == expected_offset
    assert kwargs["limit"] == expected_limit


# ---------- create_ticket_type ----------


async def test_create_allowed_for_admin(
    service, repo, admin, make_ticket_type, make_ticket_type_create
):
    data = make_ticket_type_create()
    created = make_ticket_type(id=100)
    repo.create.return_value = created

    result = await service.create_ticket_type(data, admin)

    assert result is created
    repo.create.assert_awaited_once_with(data)


async def test_create_forbidden_for_non_admin(
    service, repo, event_repo, regular_user, make_ticket_type_create
):
    with pytest.raises(PermissionDeniedError):
        await service.create_ticket_type(make_ticket_type_create(), regular_user)

    event_repo.get.assert_not_awaited()  # permission is checked first
    repo.create.assert_not_awaited()


async def test_create_event_not_found(
    service, repo, event_repo, admin, make_ticket_type_create
):
    event_repo.get.return_value = None

    with pytest.raises(NotFoundError):
        await service.create_ticket_type(make_ticket_type_create(event_id=999), admin)

    event_repo.get.assert_awaited_once_with(999)
    repo.create.assert_not_awaited()


@pytest.mark.parametrize(
    "starts_at, ends_at",
    [
        (SALES_END, SALES_START),  # reversed
        (SALES_START, SALES_START),  # zero length
        (SALES_START, SALES_START - timedelta(seconds=1)),  # ends 1s earlier
    ],
)
async def test_create_invalid_sales_window(
    service, repo, admin, make_ticket_type_create, starts_at, ends_at
):
    # validate=False bypasses the schema validator to test the service's own check
    data = make_ticket_type_create(
        validate=False, sales_start_at=starts_at, sales_end_at=ends_at
    )

    with pytest.raises(DomainValidationError):
        await service.create_ticket_type(data, admin)

    repo.create.assert_not_awaited()


@pytest.mark.parametrize(
    "starts_at, ends_at",
    [(None, None), (SALES_START, None), (None, SALES_END)],
)
async def test_create_open_ended_sales_window_allowed(
    service, repo, admin, make_ticket_type_create, make_ticket_type, starts_at, ends_at
):
    data = make_ticket_type_create(sales_start_at=starts_at, sales_end_at=ends_at)
    repo.create.return_value = make_ticket_type(id=100)

    await service.create_ticket_type(data, admin)

    repo.create.assert_awaited_once_with(data)


# ---------- update_ticket_type ----------


async def test_update_allowed_for_admin(
    service, repo, admin, ticket_type, make_ticket_type_update
):
    data = make_ticket_type_update(name="VIP")
    repo.update.return_value = ticket_type

    result = await service.update_ticket_type(1, data, admin)

    assert result is ticket_type
    repo.update.assert_awaited_once_with(ticket_type, data)


async def test_update_forbidden_for_non_admin(
    service, repo, regular_user, make_ticket_type_update
):
    with pytest.raises(PermissionDeniedError):
        await service.update_ticket_type(
            1, make_ticket_type_update(name="VIP"), regular_user
        )

    repo.update.assert_not_awaited()


async def test_update_not_found(service, repo, admin, make_ticket_type_update):
    repo.get.return_value = None

    with pytest.raises(NotFoundError):
        await service.update_ticket_type(
            999, make_ticket_type_update(name="VIP"), admin
        )

    repo.update.assert_not_awaited()


async def test_update_missing_returns_404_before_403(
    service, repo, regular_user, make_ticket_type_update
):
    repo.get.return_value = None

    with pytest.raises(NotFoundError):
        await service.update_ticket_type(
            999, make_ticket_type_update(name="VIP"), regular_user
        )


# --- sales window ---


async def test_update_without_window_fields_skips_window_check(
    service, repo, admin, ticket_type, make_ticket_type, make_ticket_type_update
):
    # even a stored window that is already invalid must not block a name change
    repo.get.return_value = make_ticket_type(
        sales_start_at=SALES_END, sales_end_at=SALES_START
    )
    data = make_ticket_type_update(name="VIP")
    repo.update.return_value = ticket_type

    await service.update_ticket_type(1, data, admin)

    repo.update.assert_awaited_once()


async def test_update_both_dates_valid(
    service, repo, admin, ticket_type, make_ticket_type_update
):
    data = make_ticket_type_update(sales_start_at=SALES_START, sales_end_at=SALES_END)
    repo.update.return_value = ticket_type

    await service.update_ticket_type(1, data, admin)

    repo.update.assert_awaited_once_with(ticket_type, data)


async def test_update_schema_rejects_reversed_window(make_ticket_type_update):
    with pytest.raises(ValidationError):
        make_ticket_type_update(sales_start_at=SALES_END, sales_end_at=SALES_START)


@pytest.mark.parametrize(
    "fields",
    [
        {"sales_start_at": SALES_START - timedelta(hours=1)},  # still before stored end
        {"sales_end_at": SALES_END + timedelta(hours=1)},  # still after stored start
    ],
)
async def test_update_single_valid_date_allowed(
    service, repo, admin, ticket_type, make_ticket_type_update, fields
):
    data = make_ticket_type_update(**fields)
    repo.update.return_value = ticket_type

    await service.update_ticket_type(1, data, admin)

    repo.update.assert_awaited_once_with(ticket_type, data)


@pytest.mark.parametrize("field", ["sales_start_at", "sales_end_at"])
async def test_update_explicit_null_clears_a_date(
    service, repo, admin, ticket_type, make_ticket_type_update, field
):
    data = make_ticket_type_update(**{field: None})  # sent as null, not omitted
    repo.update.return_value = ticket_type

    await service.update_ticket_type(1, data, admin)

    repo.update.assert_awaited_once_with(ticket_type, data)


async def test_update_start_only_allowed_when_stored_end_is_open(
    service, repo, admin, make_ticket_type, make_ticket_type_update
):
    stored = make_ticket_type(sales_start_at=None, sales_end_at=None)
    repo.get.return_value = stored
    data = make_ticket_type_update(sales_start_at=SALES_START)
    repo.update.return_value = stored

    await service.update_ticket_type(1, data, admin)

    repo.update.assert_awaited_once_with(stored, data)


# --- inventory ---


@pytest.mark.parametrize("total", [0, 29])
async def test_update_total_below_committed_rejected(
    service, repo, admin, make_ticket_type_update, total
):
    data = make_ticket_type_update(total_quantity=total)  # committed = 10 + 20 = 30

    with pytest.raises(ConflictError) as exc:
        await service.update_ticket_type(1, data, admin)

    assert exc.value.status_code == 409
    assert exc.value.code == "quantity_below_committed"
    repo.update.assert_not_awaited()


@pytest.mark.parametrize("total", [30, 31, 500])
async def test_update_total_at_or_above_committed_allowed(
    service, repo, admin, ticket_type, make_ticket_type_update, total
):
    data = make_ticket_type_update(total_quantity=total)
    repo.update.return_value = ticket_type

    await service.update_ticket_type(1, data, admin)

    repo.update.assert_awaited_once_with(ticket_type, data)


# ---------- delete_ticket_type ----------


async def test_delete_allowed_when_nothing_reserved_or_sold(
    service, repo, admin, make_ticket_type
):
    unused = make_ticket_type(reserved_quantity=0, sold_quantity=0)
    repo.get.return_value = unused

    await service.delete_ticket_type(1, admin)

    repo.delete.assert_awaited_once_with(unused)


async def test_delete_forbidden_for_non_admin(service, repo, regular_user):
    with pytest.raises(PermissionDeniedError):
        await service.delete_ticket_type(1, regular_user)

    repo.delete.assert_not_awaited()


async def test_delete_not_found(service, repo, admin):
    repo.get.return_value = None

    with pytest.raises(NotFoundError):
        await service.delete_ticket_type(999, admin)

    repo.delete.assert_not_awaited()


@pytest.mark.parametrize(
    "reserved, sold",
    [(1, 0), (0, 1), (5, 5)],
)
async def test_delete_rejected_when_in_use(
    service, repo, admin, make_ticket_type, reserved, sold
):
    repo.get.return_value = make_ticket_type(
        reserved_quantity=reserved, sold_quantity=sold
    )

    with pytest.raises(ConflictError) as exc:
        await service.delete_ticket_type(1, admin)

    assert exc.value.code == "ticket_type_in_use"
    repo.delete.assert_not_awaited()
