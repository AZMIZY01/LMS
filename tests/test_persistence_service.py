"""Tests for JSON persistence."""

from __future__ import annotations

from src.services.persistence_service import PersistenceService



def test_save_and_load_round_trip(tmp_path, service, january_date) -> None:
    success, _, loan = service.check_out_book("MEM-001", "9780132350884", january_date)
    assert success is True

    storage = PersistenceService(str(tmp_path / "library.json"))
    storage.save(service.books, service.members, service.loans, service.reservations)

    books, members, loans, reservations = storage.load()
    assert books.count() == service.books.count()
    assert members.count() == service.members.count()
    assert len(loans.get_all_loans()) == 1
    assert len(reservations.get_all_reservations()) == 0
    reloaded_member = members.find_by_id("MEM-001")
    assert reloaded_member is not None
    assert reloaded_member.get_borrowed_books() == [loan.copy_id]
