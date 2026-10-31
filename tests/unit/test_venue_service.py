import pytest

from app.core.exceptions import NotFoundError, PermissionDeniedError
from app.models.user import UserRole
from app.services.venue import MAX_PAGE_SIZE, VenueService

# ---------- get_venue ----------


async def test_get_venue_returns_venue(service, repo, venue):
    result = await service.get_venue(1)

    assert result is venue
    repo.get.assert_awaited_once_with(1)


async def test_get_venue_not_found(service, repo):
    repo.get.return_value = None

    with pytest.raises(NotFoundError) as exc:
        await service.get_venue(999)

    assert exc.value.status_code == 404


# # ---------- list_venues ----------


async def test_list_without_filters(service, repo):
    await service.list_venues()

    kwargs = repo.get_list.await_args.kwargs
    assert list(kwargs["filters"]) == []
    assert kwargs["offset"] == 0
    assert kwargs["limit"] == 20


async def test_list_builds_filters(service, repo):
    await service.list_venues(search="hall", city="Berlin")

    filters = repo.get_list.await_args.kwargs["filters"]
    assert len(filters) == 2


@pytest.mark.parametrize(
    "skip, limit, expected_offset, expected_limit",
    [
        (-5, 20, 0, 20),
        (0, 0, 0, 1),
        (0, 10_000, 0, MAX_PAGE_SIZE),
        (40, 10, 40, 10),
    ],
)
async def test_list_clamps_pagination(
    service, repo, skip, limit, expected_offset, expected_limit
):
    await service.list_venues(skip=skip, limit=limit)

    kwargs = repo.get_list.await_args.kwargs
    assert kwargs["offset"] == expected_offset
    assert kwargs["limit"] == expected_limit


# ---------- create_venue ----------


async def test_create_allowed_for_admin(service, repo, admin, venue_create, make_venue):
    created = make_venue(id=100)
    repo.create.return_value = created

    result = await service.create_venue(venue_create, admin)

    assert result is created
    repo.create.assert_awaited_once_with(venue_create, created_by=admin.id)


async def test_create_forbidden_for_non_admin(
    service, repo, regular_user, venue_create
):
    with pytest.raises(PermissionDeniedError):
        await service.create_venue(venue_create, regular_user)

    repo.create.assert_not_awaited()


# ---------- update_venue ----------


async def test_update_allowed_for_admin(service, repo, admin, venue, venue_update):
    repo.update.return_value = venue

    result = await service.update_venue(1, venue_update, admin)

    assert result is venue
    repo.update.assert_awaited_once_with(venue, venue_update)


async def test_update_forbidden_for_non_admin(
    service, repo, regular_user, venue_update
):
    with pytest.raises(PermissionDeniedError):
        await service.update_venue(1, venue_update, regular_user)

    repo.update.assert_not_awaited()


async def test_update_not_found(service, repo, admin, venue_update):
    repo.get.return_value = None

    with pytest.raises(NotFoundError):
        await service.update_venue(999, venue_update, admin)

    repo.update.assert_not_awaited()


# ---------- delete_venue ----------


async def test_delete_allowed_for_admin(service, repo, admin, venue):
    await service.delete_venue(1, admin)

    repo.delete.assert_awaited_once_with(venue)


async def test_delete_forbidden_for_non_admin(service, repo, regular_user):
    with pytest.raises(PermissionDeniedError):
        await service.delete_venue(1, regular_user)

    repo.delete.assert_not_awaited()


async def test_delete_not_found(service, repo, admin):
    repo.get.return_value = None

    with pytest.raises(NotFoundError):
        await service.delete_venue(999, admin)

    repo.delete.assert_not_awaited()


# ---------- the permission rule itself ----------


@pytest.mark.parametrize(
    "role, expected",
    [
        (UserRole.ADMIN, True),
        (UserRole.CUSTOMER, False),
    ],
)
def test_can_modify_by_role(make_user, role, expected):
    assert VenueService._can_modify(make_user(role=role)) is expected
