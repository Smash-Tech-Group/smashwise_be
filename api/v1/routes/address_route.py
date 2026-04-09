"""
api/v1/routes/address_route.py

Delivery address CRUD endpoints.

All routes require a valid JWT (Bearer token).
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils.success_response import success_response
from api.utils.jwt_handler import get_current_user
from api.v1.models.user import User
from api.v1.schemas.address import AddressCreate, AddressUpdate, AddressOut
from api.v1.services.address_service import address_service

address = APIRouter(prefix="/addresses", tags=["Addresses"])


@address.get(
    "/",
    status_code=status.HTTP_200_OK,
    summary="List all saved addresses for the authenticated user",
)
def list_addresses(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    addresses = address_service.get_all(db, user)
    data = [AddressOut.model_validate(a).model_dump() for a in addresses]
    return success_response(
        status_code=200,
        message="Addresses retrieved successfully.",
        data={"addresses": data},
    )


@address.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new delivery address",
)
def create_address(
    request: AddressCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    addr = address_service.create_address(db, user, request)
    return success_response(
        status_code=201,
        message="Address created successfully.",
        data=AddressOut.model_validate(addr).model_dump(),
    )


@address.get(
    "/{address_id}",
    status_code=status.HTTP_200_OK,
    summary="Get a single address by ID",
)
def get_address(
    address_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    addr = address_service.get_by_id(db, user, address_id)
    return success_response(
        status_code=200,
        message="Address retrieved successfully.",
        data=AddressOut.model_validate(addr).model_dump(),
    )


@address.patch(
    "/{address_id}",
    status_code=status.HTTP_200_OK,
    summary="Update an existing address",
)
def update_address(
    address_id: str,
    request: AddressUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    addr = address_service.update_address(db, user, address_id, request)
    return success_response(
        status_code=200,
        message="Address updated successfully.",
        data=AddressOut.model_validate(addr).model_dump(),
    )


@address.delete(
    "/{address_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete an address",
)
def delete_address(
    address_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    address_service.delete_address(db, user, address_id)
    return success_response(
        status_code=200,
        message="Address deleted successfully.",
    )


@address.patch(
    "/{address_id}/set-default",
    status_code=status.HTTP_200_OK,
    summary="Mark an address as the default; clears all other defaults",
)
def set_default_address(
    address_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    addr = address_service.set_default(db, user, address_id)
    return success_response(
        status_code=200,
        message="Default address updated.",
        data=AddressOut.model_validate(addr).model_dump(),
    )