"""Fine calculation service using a table-driven approach."""

from __future__ import annotations

from datetime import date

from src.models.loan import LoanRecord
from src.services.fine_configuration import FineConfiguration
from src.utils.date_helpers import days_between


class FineCalculator:
    """Calculate fines for overdue library loans."""

    def __init__(self, config: FineConfiguration | None = None) -> None:
        self.config = config or FineConfiguration()

    def calculate_fine(self, days_overdue: int) -> float:
        """Calculate a fine amount based on incremental tiered rates."""
        if days_overdue <= 0:
            return 0.0

        total = 0.0
        remaining_days = days_overdue

        for start_day, end_day, rate in self.config.rate_tiers:
            if remaining_days <= 0:
                break

            tier_span = end_day - start_day + 1
            days_in_tier = min(remaining_days, tier_span)
            total += days_in_tier * rate
            remaining_days -= days_in_tier

        return round(min(total, self.config.max_fine_per_loan), 2)

    def calculate_loan_fine(self, loan: LoanRecord, current_date: date) -> float:
        """Calculate the fine for a single loan record."""
        if not loan.is_overdue(current_date):
            return 0.0
        overdue_days = days_between(loan.due_date, current_date)
        return self.calculate_fine(overdue_days)

    def calculate_member_fines(self, loans: list[LoanRecord], current_date: date) -> float:
        """Calculate the total fine across all of a member's loans."""
        total = sum(self.calculate_loan_fine(loan, current_date) for loan in loans)
        return round(total, 2)
