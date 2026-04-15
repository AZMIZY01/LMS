"""Reporting services for the Library Management System."""

from __future__ import annotations

from collections import Counter
from datetime import date

from src.services.book_collection import BookCollection
from src.services.loan_collection import LoanCollection
from src.services.member_collection import MemberCollection
from src.services.fine_calculator import FineCalculator


class ReportService:
    """Generate reports over books, members, and loan activity."""

    def __init__(
        self,
        books: BookCollection,
        members: MemberCollection,
        loans: LoanCollection,
        fine_calculator: FineCalculator,
    ) -> None:
        self.books = books
        self.members = members
        self.loans = loans
        self.fine_calculator = fine_calculator

    def list_overdue_books(self, current_date: date) -> list[dict[str, object]]:
        """Return overdue books and their borrowing members."""
        report_rows: list[dict[str, object]] = []
        for loan in self.loans.get_overdue_loans(current_date):
            book = self.books.find_by_copy_id(loan.copy_id)
            member = self.members.find_by_id(loan.member_id)
            report_rows.append(
                {
                    "loan_id": loan.loan_id,
                    "copy_id": loan.copy_id,
                    "book_title": book.title if book else "Unknown",
                    "member_name": member.name if member else "Unknown",
                    "due_date": loan.due_date,
                    "days_overdue": max((current_date - loan.due_date).days, 0),
                    "fine": self.fine_calculator.calculate_loan_fine(loan, current_date),
                }
            )
        return report_rows


    def overdue_books(self, current_date: date) -> list[dict[str, object]]:
        """Backward-compatible alias for overdue book reporting."""
        return self.list_overdue_books(current_date)

    def members_with_outstanding_fines(self, current_date: date) -> list[dict[str, object]]:
        """Return members who currently owe fines.

        This includes both:
        - accrued fines on still-active overdue loans, and
        - previously assessed fines already stored on the member record

        Without including ``member.fines_owed``, a member disappears from the
        fines report immediately after returning an overdue book even though the
        fine was correctly charged during check-in.
        """
        rows: list[dict[str, object]] = []
        for member in self.members.get_all_members():
            loans = self.loans.get_member_loans(member.member_id, include_returned=False)
            active_loan_fines = self.fine_calculator.calculate_member_fines(loans, current_date)
            fine_total = round(member.fines_owed + active_loan_fines, 2)
            if fine_total > 0:
                rows.append(
                    {
                        "member_id": member.member_id,
                        "name": member.name,
                        "fine_total": fine_total,
                    }
                )
        rows.sort(key=lambda item: (-float(item["fine_total"]), str(item["name"])))
        return rows

    def most_borrowed_books(self, top_n: int = 5) -> list[dict[str, object]]:
        """Return the most borrowed books by total borrow count."""
        counts = Counter()
        titles: dict[str, str] = {}
        for book in self.books.get_all_books():
            counts[book.isbn] += book.borrow_count
            titles.setdefault(book.isbn, book.title)

        return [
            {"isbn": isbn, "title": titles[isbn], "borrow_count": count}
            for isbn, count in counts.most_common(top_n)
            if count > 0
        ]

    def daily_circulation_report(self, target_date: date) -> dict[str, int]:
        """Return counts of checkouts and returns for a given day."""
        checkout_count = 0
        return_count = 0
        for loan in self.loans.get_all_loans():
            if loan.checkout_date == target_date:
                checkout_count += 1
            if loan.return_date == target_date:
                return_count += 1
        return {
            "date": target_date.isoformat(),
            "checkouts": checkout_count,
            "returns": return_count,
        }
