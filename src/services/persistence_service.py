"""JSON persistence for the Library Management System."""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import date
from pathlib import Path
from typing import Any

from src.models.book import Book
from src.models.loan import LoanRecord
from src.models.member import Member
from src.models.reservation import Reservation
from src.services.book_collection import BookCollection
from src.services.loan_collection import LoanCollection
from src.services.member_collection import MemberCollection
from src.services.reservation_collection import ReservationCollection


class PersistenceService:
    """Persist library state to and from a JSON file."""

    def __init__(self, file_path: str) -> None:
        self.file_path = Path(file_path)

    def save(
        self,
        books: BookCollection,
        members: MemberCollection,
        loans: LoanCollection,
        reservations: ReservationCollection,
    ) -> None:
        """Save the current application state to disk."""
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "books": [self._serialize_book(book) for book in books.get_all_books()],
            "members": [self._serialize_member(member) for member in members.get_all_members()],
            "loans": [self._serialize_loan(loan) for loan in loans.get_all_loans()],
            "reservations": [
                self._serialize_reservation(reservation)
                for reservation in reservations.get_all_reservations()
            ],
        }
        self.file_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def load(self) -> tuple[BookCollection, MemberCollection, LoanCollection, ReservationCollection]:
        """Load application state from disk or return empty collections."""
        books = BookCollection()
        members = MemberCollection()
        loans = LoanCollection()
        reservations = ReservationCollection()

        if not self.file_path.exists():
            return books, members, loans, reservations

        payload = json.loads(self.file_path.read_text(encoding="utf-8"))

        for raw_book in payload.get("books", []):
            books.add_book(Book(**raw_book))

        for raw_member in payload.get("members", []):
            member = Member(
                name=raw_member["name"],
                member_id=raw_member["member_id"],
                email=raw_member["email"],
                phone=raw_member.get("phone", ""),
                is_active=raw_member.get("is_active", True),
            )
            member._borrowed_copy_ids = raw_member.get("_borrowed_copy_ids", [])
            member._fines_owed = raw_member.get("_fines_owed", 0.0)
            members.add_member(member)

        for raw_loan in payload.get("loans", []):
            loans.add_loan(
                LoanRecord(
                    loan_id=raw_loan["loan_id"],
                    copy_id=raw_loan["copy_id"],
                    member_id=raw_loan["member_id"],
                    checkout_date=self._parse_date(raw_loan["checkout_date"]),
                    due_date=self._parse_date(raw_loan["due_date"]),
                    return_date=self._parse_date(raw_loan.get("return_date")),
                )
            )

        for raw_reservation in payload.get("reservations", []):
            reservations.add_reservation(
                Reservation(
                    reservation_id=raw_reservation["reservation_id"],
                    copy_id=raw_reservation["copy_id"],
                    member_id=raw_reservation["member_id"],
                    reserved_on=self._parse_date(raw_reservation["reserved_on"]),
                    expires_on=self._parse_date(raw_reservation["expires_on"]),
                    notified=raw_reservation.get("notified", False),
                )
            )

        return books, members, loans, reservations

    def _serialize_book(self, book: Book) -> dict[str, Any]:
        return asdict(book)

    def _serialize_member(self, member: Member) -> dict[str, Any]:
        return asdict(member)

    def _serialize_loan(self, loan: LoanRecord) -> dict[str, Any]:
        payload = asdict(loan)
        payload["checkout_date"] = self._format_date(loan.checkout_date)
        payload["due_date"] = self._format_date(loan.due_date)
        payload["return_date"] = self._format_date(loan.return_date)
        return payload

    def _serialize_reservation(self, reservation: Reservation) -> dict[str, Any]:
        payload = asdict(reservation)
        payload["reserved_on"] = self._format_date(reservation.reserved_on)
        payload["expires_on"] = self._format_date(reservation.expires_on)
        return payload

    def _format_date(self, value: date | None) -> str | None:
        return value.isoformat() if value is not None else None

    def _parse_date(self, value: str | None) -> date | None:
        return date.fromisoformat(value) if value is not None else None
