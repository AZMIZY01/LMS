"""Tests for the main library orchestration service."""

from __future__ import annotations

from datetime import timedelta


def test_check_out_book_success(service, january_date) -> None:
    success, message, loan = service.check_out_book("MEM-001", "9780132350884", january_date)
    assert success is True
    assert message == "Book checked out successfully"
    assert loan is not None
    assert service.members.find_by_id("MEM-001").get_borrowed_books() == [loan.copy_id]



def test_check_out_book_member_not_found(service, january_date) -> None:
    success, message, loan = service.check_out_book("MEM-404", "9780132350884", january_date)
    assert success is False
    assert message == "Member not found"
    assert loan is None



def test_check_in_overdue_book_adds_fine(service, january_date) -> None:
    success, _, loan = service.check_out_book("MEM-001", "9780132350884", january_date)
    assert success is True
    return_date = loan.due_date + timedelta(days=5)

    success, message, fine = service.check_in_book(loan.copy_id, return_date)
    assert success is True
    assert message == "Book checked in successfully"
    assert fine == 2.5
    member = service.members.find_by_id("MEM-001")
    assert member.fines_owed == 2.5



def test_reservation_and_notification_flow(service, january_date) -> None:
    success, _, loan = service.check_out_book("MEM-001", "9780132350884", january_date)
    assert success is True

    success, message, reservation = service.reserve_book("MEM-002", loan.copy_id, january_date)
    assert success is True
    assert message == "Reservation created successfully"
    assert reservation is not None

    success, _, _ = service.check_in_book(loan.copy_id, january_date + timedelta(days=1))
    assert success is True
    messages = service.notifications.get_messages()
    assert any("Reserved book available" in message for message in messages)



def test_generate_overdue_notifications(service, january_date) -> None:
    success, _, loan = service.check_out_book("MEM-001", "9781593279288", january_date)
    assert success is True
    messages = service.generate_overdue_notifications(loan.due_date + timedelta(days=2))
    assert len(messages) == 1
    assert "Overdue notice" in messages[0]
