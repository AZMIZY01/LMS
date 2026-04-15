"""Loan model for the Library Management System."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class LoanRecord:
    """Represent a single book loan transaction."""

    loan_id: str
    copy_id: str
    member_id: str
    checkout_date: date
    due_date: date
    return_date: Optional[date] = None

    def is_active(self) -> bool:
        """Return True if the loan has not been returned yet."""
        return self.return_date is None

    def is_overdue(self, current_date: date) -> bool:
        """Return True if the active loan is overdue."""
        return self.is_active() and current_date > self.due_date

    def mark_returned(self, return_date: date) -> None:
        """Record the date that the loan was returned."""
        if return_date < self.checkout_date:
            raise ValueError("Return date cannot be before checkout date")
        self.return_date = return_date
