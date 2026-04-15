"""Member model for the Library Management System."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from src.constants import MAX_BORROW_LIMIT, MAX_FINE_BEFORE_SUSPENSION


@dataclass
class Member:
    """Represent a library member and their borrowing state."""

    name: str
    member_id: str
    email: str
    phone: str = ""
    is_active: bool = True
    _borrowed_copy_ids: List[str] = field(default_factory=list)
    _fines_owed: float = 0.0

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Member name cannot be empty")
        if not self.member_id.strip():
            raise ValueError("Member ID cannot be empty")
        if "@" not in self.email or self.email.startswith("@") or self.email.endswith("@"):
            raise ValueError("Invalid email address")

    @property
    def fines_owed(self) -> float:
        """Return the amount of unpaid fines."""
        return round(self._fines_owed, 2)

    def can_borrow(self) -> bool:
        """Return True if the member is currently eligible to borrow."""
        has_room = len(self._borrowed_copy_ids) < MAX_BORROW_LIMIT
        acceptable_fines = self._fines_owed < MAX_FINE_BEFORE_SUSPENSION
        return self.is_active and has_room and acceptable_fines

    def borrow_book(self, copy_id: str) -> bool:
        """Register a borrowed book copy for the member."""
        if not self.can_borrow():
            return False
        if copy_id in self._borrowed_copy_ids:
            return False
        self._borrowed_copy_ids.append(copy_id)
        return True

    def return_book(self, copy_id: str) -> bool:
        """Remove a returned book copy from the member record."""
        if copy_id not in self._borrowed_copy_ids:
            return False
        self._borrowed_copy_ids.remove(copy_id)
        return True

    def get_borrowed_books(self) -> list[str]:
        """Return a defensive copy of borrowed copy identifiers."""
        return self._borrowed_copy_ids.copy()

    def add_fine(self, amount: float) -> None:
        """Add a positive fine amount to the member account."""
        if amount < 0:
            raise ValueError("Fine amount cannot be negative")
        self._fines_owed = round(self._fines_owed + amount, 2)

    def pay_fine(self, amount: float) -> float:
        """Pay part or all of the member's fines and return the applied payment."""
        if amount < 0:
            raise ValueError("Payment amount cannot be negative")
        paid_amount = min(amount, self._fines_owed)
        self._fines_owed = round(self._fines_owed - paid_amount, 2)
        return round(paid_amount, 2)
