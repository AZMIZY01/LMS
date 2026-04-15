"""Reservation model for the Library Management System."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass
class Reservation:
    """Represent a reservation request for a book copy."""

    reservation_id: str
    copy_id: str
    member_id: str
    reserved_on: date
    expires_on: date
    notified: bool = False

    def is_active(self, current_date: date) -> bool:
        """Return True if the reservation has not expired."""
        return current_date <= self.expires_on
