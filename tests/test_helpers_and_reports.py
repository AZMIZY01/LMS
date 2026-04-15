"""Tests for helpers, reports, and remaining collection behavior."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from src.models.book import Book
from src.models.loan import LoanRecord
from src.models.member import Member
from src.services.book_collection import BookCollection
from src.services.loan_collection import LoanCollection
from src.services.member_collection import MemberCollection
from src.services.report_service import ReportService
from src.services.reservation_collection import ReservationCollection
from src.services.fine_calculator import FineCalculator
from src.models.reservation import Reservation
from src.utils.date_helpers import (
    calculate_due_date,
    days_between,
    format_date_for_display,
    is_date_in_past,
    parse_date_string,
)
from src.utils.string_helpers import (
    format_book_display,
    normalize_search_term,
    validate_email,
)



def test_book_model_status_transitions() -> None:
    book = Book("Test Book", "Author", "123", 2020, "COPY-1")
    assert book.is_available() is True
    book.check_out()
    assert book.status == "checked_out"
    book.check_in()
    assert book.status == "available"
    book.mark_reserved()
    assert book.status == "reserved"
    book.mark_lost()
    assert book.status == "lost"



def test_reference_book_cannot_be_checked_out_or_reserved() -> None:
    book = Book("Ref Book", "Author", "1234", 2020, "COPY-2", is_reference_only=True)
    assert book.is_available() is False
    with pytest.raises(ValueError):
        book.mark_reserved()



def test_loan_mark_returned_validates_dates() -> None:
    loan = LoanRecord("LOAN-1", "COPY-1", "MEM-1", date(2026, 1, 10), date(2026, 1, 20))
    with pytest.raises(ValueError):
        loan.mark_returned(date(2026, 1, 9))



def test_member_validation_and_copy_semantics() -> None:
    with pytest.raises(ValueError):
        Member("", "MEM-1", "user@example.com")
    member = Member("Alice", "MEM-1", "alice@example.com")
    member.borrow_book("COPY-1")
    borrowed = member.get_borrowed_books()
    borrowed.append("COPY-2")
    assert member.get_borrowed_books() == ["COPY-1"]
    with pytest.raises(ValueError):
        member.pay_fine(-1)



def test_member_collection_operations() -> None:
    collection = MemberCollection()
    member = Member("Alice", "MEM-1", "alice@example.com")
    collection.add_member(member)
    assert collection.find_by_id("MEM-1") == member
    assert collection.find_by_name("ali") == [member]
    assert collection.count() == 1
    with pytest.raises(ValueError):
        collection.add_member(member)
    with pytest.raises(ValueError):
        member.borrow_book("COPY-1")
        collection.remove_member("MEM-1")



def test_loan_and_reservation_collections() -> None:
    loans = LoanCollection()
    loan = LoanRecord("LOAN-1", "COPY-1", "MEM-1", date(2026, 1, 1), date(2026, 1, 10))
    loans.add_loan(loan)
    assert loans.find_by_id("LOAN-1") == loan
    assert loans.get_active_loan_for_copy("COPY-1") == loan
    assert loans.get_member_loans("MEM-1", include_returned=False) == [loan]
    assert loans.get_overdue_loans(date(2026, 1, 12)) == [loan]

    reservations = ReservationCollection()
    reservation = Reservation("RES-1", "COPY-1", "MEM-2", date(2026, 1, 12), date(2026, 1, 20))
    reservations.add_reservation(reservation)
    assert reservations.get_member_reservations("MEM-2", date(2026, 1, 13)) == [reservation]
    assert reservations.get_active_reservations_for_copy("COPY-1", date(2026, 1, 13)) == [reservation]
    reservations.purge_expired(date(2026, 1, 25))
    assert reservations.get_all_reservations() == []



def test_date_and_string_helpers() -> None:
    checkout = date(2026, 1, 1)
    assert calculate_due_date(checkout, 14) == date(2026, 1, 15)
    assert days_between(date(2026, 1, 1), date(2026, 1, 3)) == 2
    assert is_date_in_past(date(2026, 1, 1), date(2026, 1, 2)) is True
    assert format_date_for_display(date(2026, 1, 5)) == "2026-01-05"
    assert format_date_for_display(None) == "N/A"
    assert parse_date_string("2026-01-05") == date(2026, 1, 5)
    book = Book("Clean Code", "Robert C. Martin", "9780132350884", 2008, "COPY-1")
    assert "Clean Code" in format_book_display(book)
    assert normalize_search_term("  PyThOn  ") == "python"
    assert validate_email("user@example.com") is True
    assert validate_email("bad-email") is False



def test_report_service_outputs(service, january_date) -> None:
    success, _, loan_one = service.check_out_book("MEM-001", "9780132350884", january_date)
    assert success is True
    success, _, loan_two = service.check_out_book("MEM-002", "9781593279288", january_date)
    assert success is True

    service.check_in_book(loan_one.copy_id, january_date + timedelta(days=1))
    overdue_date = loan_two.due_date + timedelta(days=3)

    overdue_rows = service.report_service.list_overdue_books(overdue_date)
    assert len(overdue_rows) == 1
    assert overdue_rows[0]["member_name"] == "Bob Smith"

    fine_rows = service.report_service.members_with_outstanding_fines(overdue_date)
    assert len(fine_rows) == 1
    assert fine_rows[0]["name"] == "Bob Smith"

    popular_rows = service.report_service.most_borrowed_books()
    assert popular_rows[0]["borrow_count"] >= 1

    daily_row = service.report_service.daily_circulation_report(january_date)
    assert daily_row["checkouts"] == 2


def test_fines_report_includes_stored_member_fines_after_return(service, january_date) -> None:
    success, _, loan = service.check_out_book("MEM-001", "9780132350884", january_date)
    assert success is True

    report_date = loan.due_date + timedelta(days=5)
    success, _, fine = service.check_in_book(loan.copy_id, report_date)
    assert success is True
    assert fine == 2.5

    fine_rows = service.report_service.members_with_outstanding_fines(report_date)
    assert len(fine_rows) == 1
    assert fine_rows[0]["member_id"] == "MEM-001"
    assert fine_rows[0]["fine_total"] == 2.5



def test_book_collection_update_and_remove() -> None:
    collection = BookCollection()
    book = Book("Old", "Author", "123", 2020, "COPY-1")
    collection.add_book(book)
    updated = collection.update_book("COPY-1", title="New")
    assert updated.title == "New"
    collection.remove_book("COPY-1")
    assert collection.count() == 0
    with pytest.raises(KeyError):
        collection.remove_book("COPY-404")
