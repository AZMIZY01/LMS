"""Reservation collection ADT for managing reservations."""

from __future__ import annotations

from datetime import date

from src.models.reservation import Reservation


class ReservationCollection:
    """ADT for managing reservations in queue order."""

    def __init__(self) -> None:
        self._reservations: dict[str, Reservation] = {}

    def add_reservation(self, reservation: Reservation) -> None:
        """Add a reservation."""
        if reservation.reservation_id in self._reservations:
            raise ValueError(f"Reservation {reservation.reservation_id} already exists")
        self._reservations[reservation.reservation_id] = reservation

    def get_active_reservations_for_copy(
        self,
        copy_id: str,
        current_date: date,
    ) -> list[Reservation]:
        """Return active reservations for a copy ordered by reserve time."""
        reservations = [
            reservation
            for reservation in self._reservations.values()
            if reservation.copy_id == copy_id and reservation.is_active(current_date)
        ]
        reservations.sort(key=lambda item: (item.reserved_on, item.reservation_id))
        return reservations

    def get_member_reservations(self, member_id: str, current_date: date) -> list[Reservation]:
        """Return active reservations for a member."""
        return [
            reservation
            for reservation in self._reservations.values()
            if reservation.member_id == member_id and reservation.is_active(current_date)
        ]

    def remove_reservation(self, reservation_id: str) -> None:
        """Remove a reservation by ID."""
        if reservation_id not in self._reservations:
            raise KeyError(f"Reservation {reservation_id} not found")
        del self._reservations[reservation_id]

    def purge_expired(self, current_date: date) -> None:
        """Remove expired reservations."""
        expired_ids = [
            reservation_id
            for reservation_id, reservation in self._reservations.items()
            if not reservation.is_active(current_date)
        ]
        for reservation_id in expired_ids:
            del self._reservations[reservation_id]

    def get_all_reservations(self) -> list[Reservation]:
        """Return all reservations."""
        return list(self._reservations.values())
