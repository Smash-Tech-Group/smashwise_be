"""
api/v1/services/address_service.py

Business logic for UserAddress CRUD.

Rules enforced here (not at the DB level):
  - A user can only access / modify their own addresses.
  - At most ONE address per user can have is_default=True.
    Setting a new default automatically clears all others.
"""

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from api.core.base.services import Service
from api.v1.models.address import UserAddress
from api.v1.models.user import User
from api.v1.schemas.address import AddressCreate, AddressUpdate


class AddressService(Service):
    # ── Abstract method stubs (required by Service base) ──────────
    def create(self): pass
    def fetch(self): pass
    def fetch_all(self): pass
    def update(self): pass
    def delete(self): pass

    # ── Helpers ───────────────────────────────────────────────────

    def _get_owned(self, db: Session, user: User, address_id: str) -> UserAddress:
        """Return the address or raise 404; also raise 403 if not owned."""
        addr = db.query(UserAddress).filter(UserAddress.id == address_id).first()
        if not addr:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Address not found.",
            )
        if addr.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this address.",
            )
        return addr

    def _clear_defaults(self, db: Session, user_id: str) -> None:
        """Unset is_default for all addresses belonging to the user."""
        db.query(UserAddress).filter(
            UserAddress.user_id == user_id,
            UserAddress.is_default.is_(True),
        ).update({"is_default": False}, synchronize_session=False)

    # ── Public service methods ────────────────────────────────────

    def get_all(self, db: Session, user: User) -> list[UserAddress]:
        return (
            db.query(UserAddress)
            .filter(UserAddress.user_id == user.id)
            .order_by(UserAddress.created_at.desc())
            .all()
        )

    def get_by_id(self, db: Session, user: User, address_id: str) -> UserAddress:
        return self._get_owned(db, user, address_id)

    def create_address(self, db: Session, user: User, data: AddressCreate) -> UserAddress:
        # If this is the first address OR caller explicitly wants it as default,
        # clear any existing default first.
        existing_count = (
            db.query(UserAddress).filter(UserAddress.user_id == user.id).count()
        )
        make_default = data.is_default or existing_count == 0

        if make_default:
            self._clear_defaults(db, user.id)

        addr = UserAddress(
            user_id=user.id,
            category=data.category,
            name=data.name,
            contact_person=data.contact_person,
            address=data.address,
            is_default=make_default,
        )
        db.add(addr)
        db.commit()
        db.refresh(addr)
        return addr

    def update_address(
        self,
        db: Session,
        user: User,
        address_id: str,
        data: AddressUpdate,
    ) -> UserAddress:
        addr = self._get_owned(db, user, address_id)

        if data.category is not None:
            addr.category = data.category
        if data.name is not None:
            addr.name = data.name
        if data.contact_person is not None:
            addr.contact_person = data.contact_person
        if data.address is not None:
            addr.address = data.address
        if data.is_default is True:
            self._clear_defaults(db, user.id)
            addr.is_default = True
        elif data.is_default is False:
            addr.is_default = False

        db.commit()
        db.refresh(addr)
        return addr

    def delete_address(self, db: Session, user: User, address_id: str) -> None:
        addr = self._get_owned(db, user, address_id)
        db.delete(addr)
        db.commit()

    def set_default(self, db: Session, user: User, address_id: str) -> UserAddress:
        addr = self._get_owned(db, user, address_id)
        self._clear_defaults(db, user.id)
        addr.is_default = True
        db.commit()
        db.refresh(addr)
        return addr


address_service = AddressService()