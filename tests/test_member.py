"""Tests for the Member model."""

from __future__ import annotations

import pytest

from src.constants import MAX_BORROW_LIMIT
from src.models.member import Member


class TestMember:
    """Verify member borrowing and fine behaviors."""

    def test_member_can_borrow_until_limit(self) -> None:
        member = Member("Alice", "MEM-1", "alice@example.com")
        for index in range(MAX_BORROW_LIMIT):
            assert member.borrow_book(f"COPY-{index}") is True
        assert member.borrow_book("COPY-999") is False

    def test_member_return_book(self) -> None:
        member = Member("Alice", "MEM-1", "alice@example.com")
        member.borrow_book("COPY-1")
        assert member.return_book("COPY-1") is True
        assert member.return_book("COPY-1") is False

    def test_member_fine_payment_cannot_go_below_zero(self) -> None:
        member = Member("Alice", "MEM-1", "alice@example.com")
        member.add_fine(12.5)
        assert member.pay_fine(20.0) == 12.5
        assert member.fines_owed == 0.0

    def test_negative_fine_raises_error(self) -> None:
        member = Member("Alice", "MEM-1", "alice@example.com")
        with pytest.raises(ValueError):
            member.add_fine(-1)
