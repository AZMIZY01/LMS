"""Loan collection ADT for managing loan records."""

from __future__ import annotations

from datetime import date

from src.models.loan import LoanRecord


class LoanCollection:
    """ADT for managing library loans."""

    def __init__(self) -> None:
        self._loans: dict[str, LoanRecord] = {}

    def add_loan(self, loan: LoanRecord) -> None:
        """Add a new loan to the registry."""
        if loan.loan_id in self._loans:
            raise ValueError(f"Loan {loan.loan_id} already exists")
        self._loans[loan.loan_id] = loan

    def find_by_id(self, loan_id: str) -> LoanRecord | None:
        """Find a loan by ID."""
        return self._loans.get(loan_id)

    def get_active_loan_for_copy(self, copy_id: str) -> LoanRecord | None:
        """Return the active loan for the given copy, if any."""
        for loan in self._loans.values():
            if loan.copy_id == copy_id and loan.is_active():
                return loan
        return None

    def get_member_loans(self, member_id: str, include_returned: bool = True) -> list[LoanRecord]:
        """Return loans for a member, optionally excluding returned ones."""
        loans = [loan for loan in self._loans.values() if loan.member_id == member_id]
        if include_returned:
            return loans
        return [loan for loan in loans if loan.is_active()]

    def get_all_loans(self) -> list[LoanRecord]:
        """Return all loan records."""
        return list(self._loans.values())

    def get_overdue_loans(self, current_date: date) -> list[LoanRecord]:
        """Return all overdue active loans."""
        return [loan for loan in self._loans.values() if loan.is_overdue(current_date)]
