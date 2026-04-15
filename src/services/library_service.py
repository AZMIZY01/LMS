"""Main orchestration service for the Library Management System."""

from __future__ import annotations

from datetime import date, timedelta

from src.constants import DEFAULT_LOAN_PERIOD_DAYS, RESERVATION_EXPIRY_DAYS
from src.models.book import Book
from src.models.loan import LoanRecord
from src.models.member import Member
from src.models.reservation import Reservation
from src.services.book_collection import BookCollection
from src.services.fine_calculator import FineCalculator
from src.services.loan_collection import LoanCollection
from src.services.member_collection import MemberCollection
from src.services.notification_service import NotificationService
from src.services.report_service import ReportService
from src.services.reservation_collection import ReservationCollection
from src.utils.date_helpers import calculate_due_date


class LibraryService:
    """Coordinate LMS operations across models and collections."""

    def __init__(
        self,
        books: BookCollection | None = None,
        members: MemberCollection | None = None,
        loans: LoanCollection | None = None,
        reservations: ReservationCollection | None = None,
        fine_calculator: FineCalculator | None = None,
        notifications: NotificationService | None = None,
    ) -> None:
        self.books = books or BookCollection()
        self.members = members or MemberCollection()
        self.loans = loans or LoanCollection()
        self.reservations = reservations or ReservationCollection()
        self.fine_calculator = fine_calculator or FineCalculator()
        self.notifications = notifications or NotificationService()
        self.report_service = ReportService(
            self.books,
            self.members,
            self.loans,
            self.fine_calculator,
        )

    def add_book(
        self,
        title: str,
        author: str,
        isbn: str,
        publication_year: int,
        copy_id: str,
        is_reference_only: bool = False,
    ) -> Book:
        """Create and store a new book copy."""
        book = Book(
            title=title,
            author=author,
            isbn=isbn,
            publication_year=publication_year,
            copy_id=copy_id,
            is_reference_only=is_reference_only,
        )
        self.books.add_book(book)
        return book

    def edit_book(self, copy_id: str, **changes: object) -> Book:
        """Update an existing book."""
        return self.books.update_book(copy_id, **changes)

    def delete_book(self, copy_id: str) -> None:
        """Delete a book if it is not on active loan."""
        active_loan = self.loans.get_active_loan_for_copy(copy_id)
        if active_loan is not None:
            raise ValueError("Cannot delete a book with an active loan")
        self.books.remove_book(copy_id)

    def search_books(self, criteria: dict[str, object]) -> list[Book]:
        """Search books by ranked criteria."""
        return self.books.search(criteria)

    def register_member(self, name: str, member_id: str, email: str, phone: str = "") -> Member:
        """Create and store a new member."""
        member = Member(name=name, member_id=member_id, email=email, phone=phone)
        self.members.add_member(member)
        return member

    def update_member(self, member_id: str, **changes: object) -> Member:
        """Update member details."""
        member = self.members.find_by_id(member_id)
        if member is None:
            raise KeyError(f"Member {member_id} not found")

        allowed_fields = {"name", "email", "phone", "is_active"}
        for field_name, value in changes.items():
            if field_name not in allowed_fields:
                raise ValueError(f"Unsupported field: {field_name}")
            setattr(member, field_name, value)
        return member

    def remove_member(self, member_id: str) -> None:
        """Remove a member record."""
        self.members.remove_member(member_id)

    def check_out_book(
        self,
        member_id: str,
        isbn: str,
        checkout_date: date | None = None,
    ) -> tuple[bool, str, LoanRecord | None]:
        """Check out an available copy of a book to a member."""
        current_date = checkout_date or date.today()
        member = self.members.find_by_id(member_id)
        if member is None:
            return False, "Member not found", None

        available_copy = self.books.find_available_copy_by_isbn(isbn)
        if available_copy is None:
            return False, "No available copy found for this ISBN", None

        if not member.can_borrow():
            return False, "Member is not eligible to borrow", None

        reservation_queue = self.reservations.get_active_reservations_for_copy(
            available_copy.copy_id,
            current_date,
        )
        if reservation_queue and reservation_queue[0].member_id != member_id:
            return False, "Book is reserved for another member", None

        due_date = calculate_due_date(current_date, DEFAULT_LOAN_PERIOD_DAYS)
        loan = LoanRecord(
            loan_id=f"LOAN-{len(self.loans.get_all_loans()) + 1}",
            copy_id=available_copy.copy_id,
            member_id=member_id,
            checkout_date=current_date,
            due_date=due_date,
        )

        available_copy.check_out()
        if not member.borrow_book(available_copy.copy_id):
            available_copy.check_in()
            return False, "Member could not borrow the selected book", None

        self.loans.add_loan(loan)

        if reservation_queue and reservation_queue[0].member_id == member_id:
            self.reservations.remove_reservation(reservation_queue[0].reservation_id)

        return True, "Book checked out successfully", loan

    def check_in_book(
        self,
        copy_id: str,
        return_date: date | None = None,
    ) -> tuple[bool, str, float]:
        """Return a checked-out book and calculate any fine."""
        current_date = return_date or date.today()
        active_loan = self.loans.get_active_loan_for_copy(copy_id)
        if active_loan is None:
            return False, "No active loan found for this copy", 0.0

        book = self.books.find_by_copy_id(copy_id)
        member = self.members.find_by_id(active_loan.member_id)
        if book is None or member is None:
            return False, "Associated book or member record is missing", 0.0

        fine_amount = self.fine_calculator.calculate_loan_fine(active_loan, current_date)
        active_loan.mark_returned(current_date)
        member.return_book(copy_id)
        book.check_in()
        if fine_amount > 0:
            member.add_fine(fine_amount)

        self._notify_next_reserver(copy_id, current_date)
        return True, "Book checked in successfully", fine_amount

    def reserve_book(
        self,
        member_id: str,
        copy_id: str,
        reservation_date: date | None = None,
    ) -> tuple[bool, str, Reservation | None]:
        """Reserve a book copy for a member."""
        current_date = reservation_date or date.today()
        member = self.members.find_by_id(member_id)
        if member is None:
            return False, "Member not found", None

        book = self.books.find_by_copy_id(copy_id)
        if book is None:
            return False, "Book copy not found", None
        if not book.can_be_reserved():
            return False, "Book cannot be reserved in its current state", None

        current_reservations = self.reservations.get_active_reservations_for_copy(copy_id, current_date)
        if any(reservation.member_id == member_id for reservation in current_reservations):
            return False, "Member already has an active reservation for this copy", None

        reservation = Reservation(
            reservation_id=f"RES-{len(self.reservations.get_all_reservations()) + 1}",
            copy_id=copy_id,
            member_id=member_id,
            reserved_on=current_date,
            expires_on=current_date + timedelta(days=RESERVATION_EXPIRY_DAYS),
        )
        self.reservations.add_reservation(reservation)
        book.mark_reserved()
        return True, "Reservation created successfully", reservation

    def pay_member_fine(self, member_id: str, amount: float) -> float:
        """Apply a fine payment and return the amount paid."""
        member = self.members.find_by_id(member_id)
        if member is None:
            raise KeyError(f"Member {member_id} not found")
        return member.pay_fine(amount)

    def get_member_borrowing_history(self, member_id: str) -> list[LoanRecord]:
        """Return all historical loans for a member."""
        if self.members.find_by_id(member_id) is None:
            raise KeyError(f"Member {member_id} not found")
        return self.loans.get_member_loans(member_id, include_returned=True)

    def get_outstanding_fine(self, member_id: str, current_date: date | None = None) -> float:
        """Calculate current outstanding fines for active overdue loans."""
        member = self.members.find_by_id(member_id)
        if member is None:
            raise KeyError(f"Member {member_id} not found")
        reference_date = current_date or date.today()
        loans = self.loans.get_member_loans(member_id, include_returned=False)
        return self.fine_calculator.calculate_member_fines(loans, reference_date) + member.fines_owed

    def generate_overdue_notifications(self, current_date: date | None = None) -> list[str]:
        """Generate overdue notices for active overdue loans."""
        reference_date = current_date or date.today()
        messages: list[str] = []
        for loan in self.loans.get_overdue_loans(reference_date):
            member = self.members.find_by_id(loan.member_id)
            book = self.books.find_by_copy_id(loan.copy_id)
            if member is None or book is None:
                continue
            fine_amount = self.fine_calculator.calculate_loan_fine(loan, reference_date)
            message = (
                f"Overdue notice: '{book.title}' is overdue. Current fine: ${fine_amount:.2f}."
            )
            self.notifications.notify(member.email, message)
            messages.append(message)
        return messages

    def _notify_next_reserver(self, copy_id: str, current_date: date) -> None:
        """Notify the next eligible reserver when a book is returned."""
        self.reservations.purge_expired(current_date)
        queue = self.reservations.get_active_reservations_for_copy(copy_id, current_date)
        if not queue:
            return

        next_reservation = queue[0]
        member = self.members.find_by_id(next_reservation.member_id)
        book = self.books.find_by_copy_id(copy_id)
        if member is None or book is None:
            return

        self.notifications.notify(
            member.email,
            f"Reserved book available: '{book.title}' is ready for checkout until "
            f"{next_reservation.expires_on.isoformat()}.",
        )

    def seed_sample_data(self) -> None:
        """Populate the system with a small sample dataset."""
        if self.books.count() > 0 or self.members.count() > 0:
            return

        self.add_book("Clean Code", "Robert C. Martin", "9780132350884", 2008, "COPY-001")
        self.add_book("Clean Code", "Robert C. Martin", "9780132350884", 2008, "COPY-002")
        self.add_book("Python Crash Course", "Eric Matthes", "9781593279288", 2019, "COPY-003")
        self.add_book("Introduction to Algorithms", "Cormen et al.", "9780262046305", 2022, "COPY-004")

        self.register_member("Alice Johnson", "MEM-001", "alice@example.com", "555-0101")
        self.register_member("Bob Smith", "MEM-002", "bob@example.com", "555-0102")
