"""Tests for fine calculation behavior."""

from __future__ import annotations

from datetime import date

from src.models.loan import LoanRecord
from src.services.fine_calculator import FineCalculator


class TestFineCalculator:
    """Verify tiered fine calculation rules."""

    def test_zero_or_negative_days_have_no_fine(self) -> None:
        calculator = FineCalculator()
        assert calculator.calculate_fine(0) == 0.0
        assert calculator.calculate_fine(-3) == 0.0

    def test_first_tier_fine(self) -> None:
        calculator = FineCalculator()
        assert calculator.calculate_fine(5) == 2.5

    def test_multi_tier_fine(self) -> None:
        calculator = FineCalculator()
        assert calculator.calculate_fine(10) == 6.5
        assert calculator.calculate_fine(35) == 36.5

    def test_calculate_loan_fine(self) -> None:
        calculator = FineCalculator()
        loan = LoanRecord(
            loan_id="LOAN-1",
            copy_id="COPY-001",
            member_id="MEM-001",
            checkout_date=date(2026, 1, 1),
            due_date=date(2026, 1, 10),
        )
        assert calculator.calculate_loan_fine(loan, date(2026, 1, 15)) == 2.5
