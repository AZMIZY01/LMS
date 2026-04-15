"""Command-line interface for the Library Management System."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from src.constants import PERSISTENCE_FILE
from src.services.library_service import LibraryService
from src.services.persistence_service import PersistenceService
from src.utils.date_helpers import parse_date_string
from src.utils.string_helpers import format_book_display


class LibraryCLI:
    """Interactive command-line interface for the LMS."""

    def __init__(self) -> None:
        self.persistence = PersistenceService(self._resolve_data_path())
        books, members, loans, reservations = self.persistence.load()
        self.service = LibraryService(books=books, members=members, loans=loans, reservations=reservations)
        if self.service.books.count() == 0 and self.service.members.count() == 0:
            self.service.seed_sample_data()

    def _resolve_data_path(self) -> str:
        project_root = Path(__file__).resolve().parent
        return str(project_root / PERSISTENCE_FILE)

    def run(self) -> None:
        """Run the CLI main loop."""
        print("\nWelcome to the Library Management System")
        while True:
            self._display_main_menu()
            choice = input("Select an option: ").strip()

            match choice:
                case "1":
                    self._book_menu()
                case "2":
                    self._member_menu()
                case "3":
                    self._loan_menu()
                case "4":
                    self._reports_menu()
                case "5":
                    self._save_and_exit()
                    break
                case _:
                    print("Invalid choice. Please try again.")

    def _display_main_menu(self) -> None:
        print(
            "\nMain Menu\n"
            "1. Book Management\n"
            "2. Member Management\n"
            "3. Loan Management\n"
            "4. Reports\n"
            "5. Save and Exit"
        )

    def _book_menu(self) -> None:
        while True:
            print(
                "\nBook Management\n"
                "1. Add book\n"
                "2. Edit book\n"
                "3. Delete book\n"
                "4. Search books\n"
                "5. List all books\n"
                "6. Back"
            )
            choice = input("Select an option: ").strip()

            match choice:
                case "1":
                    self._add_book()
                case "2":
                    self._edit_book()
                case "3":
                    self._delete_book()
                case "4":
                    self._search_books()
                case "5":
                    self._list_books(self.service.books.get_all_books())
                case "6":
                    return
                case _:
                    print("Invalid choice.")

    def _member_menu(self) -> None:
        while True:
            print(
                "\nMember Management\n"
                "1. Register member\n"
                "2. Update member\n"
                "3. View member borrowing history\n"
                "4. List members\n"
                "5. Pay fine\n"
                "6. Back"
            )
            choice = input("Select an option: ").strip()

            match choice:
                case "1":
                    self._register_member()
                case "2":
                    self._update_member()
                case "3":
                    self._view_member_history()
                case "4":
                    self._list_members()
                case "5":
                    self._pay_fine()
                case "6":
                    return
                case _:
                    print("Invalid choice.")

    def _loan_menu(self) -> None:
        while True:
            print(
                "\nLoan Management\n"
                "1. Check out book\n"
                "2. Check in book\n"
                "3. Reserve checked-out book\n"
                "4. Generate overdue notifications\n"
                "5. Back"
            )
            choice = input("Select an option: ").strip()

            match choice:
                case "1":
                    self._check_out_book()
                case "2":
                    self._check_in_book()
                case "3":
                    self._reserve_book()
                case "4":
                    self._generate_overdue_notifications()
                case "5":
                    return
                case _:
                    print("Invalid choice.")

    def _reports_menu(self) -> None:
        while True:
            print(
                "\nReports\n"
                "1. Overdue books\n"
                "2. Most borrowed books\n"
                "3. Members with outstanding fines\n"
                "4. Daily circulation report\n"
                "5. Back"
            )
            choice = input("Select an option: ").strip()

            match choice:
                case "1":
                    self._report_overdue_books()
                case "2":
                    self._report_most_borrowed_books()
                case "3":
                    self._report_members_with_fines()
                case "4":
                    self._report_daily_circulation()
                case "5":
                    return
                case _:
                    print("Invalid choice.")

    def _add_book(self) -> None:
        try:
            title = input("Title: ").strip()
            author = input("Author: ").strip()
            isbn = input("ISBN: ").strip()
            publication_year = int(input("Publication year: ").strip())
            copy_id = input("Copy ID: ").strip()
            is_reference_only = input("Reference only? (y/n): ").strip().lower() == "y"
            book = self.service.add_book(
                title,
                author,
                isbn,
                publication_year,
                copy_id,
                is_reference_only,
            )
            print(f"Added: {format_book_display(book)}")
        except Exception as error:
            print(f"Could not add book: {error}")

    def _edit_book(self) -> None:
        copy_id = input("Copy ID to edit: ").strip()
        title = input("New title (blank to keep): ").strip()
        author = input("New author (blank to keep): ").strip()
        year = input("New year (blank to keep): ").strip()
        changes: dict[str, object] = {}
        if title:
            changes["title"] = title
        if author:
            changes["author"] = author
        if year:
            changes["publication_year"] = int(year)

        try:
            book = self.service.edit_book(copy_id, **changes)
            print(f"Updated: {format_book_display(book)}")
        except Exception as error:
            print(f"Could not update book: {error}")

    def _delete_book(self) -> None:
        copy_id = input("Copy ID to delete: ").strip()
        try:
            self.service.delete_book(copy_id)
            print("Book deleted successfully.")
        except Exception as error:
            print(f"Could not delete book: {error}")

    def _search_books(self) -> None:
        title = input("Title contains: ").strip()
        author = input("Author contains: ").strip()
        isbn = input("ISBN: ").strip()
        year = input("Year: ").strip()
        criteria: dict[str, object] = {
            "title": title,
            "author": author,
            "isbn": isbn,
            "year": year or None,
        }
        results = self.service.search_books(criteria)
        self._list_books(results)

    def _register_member(self) -> None:
        try:
            member = self.service.register_member(
                name=input("Name: ").strip(),
                member_id=input("Member ID: ").strip(),
                email=input("Email: ").strip(),
                phone=input("Phone: ").strip(),
            )
            print(f"Registered member: {member.name} ({member.member_id})")
        except Exception as error:
            print(f"Could not register member: {error}")

    def _update_member(self) -> None:
        member_id = input("Member ID: ").strip()
        name = input("New name (blank to keep): ").strip()
        email = input("New email (blank to keep): ").strip()
        phone = input("New phone (blank to keep): ").strip()
        changes: dict[str, object] = {}
        if name:
            changes["name"] = name
        if email:
            changes["email"] = email
        if phone:
            changes["phone"] = phone

        try:
            member = self.service.update_member(member_id, **changes)
            print(f"Updated member: {member.name} ({member.member_id})")
        except Exception as error:
            print(f"Could not update member: {error}")

    def _view_member_history(self) -> None:
        member_id = input("Member ID: ").strip()
        try:
            history = self.service.get_member_borrowing_history(member_id)
            if not history:
                print("No borrowing history found.")
                return
            for loan in history:
                print(
                    f"Loan {loan.loan_id} | Copy {loan.copy_id} | "
                    f"Out: {loan.checkout_date} | Due: {loan.due_date} | Returned: {loan.return_date or 'No'}"
                )
        except Exception as error:
            print(f"Could not retrieve history: {error}")

    def _list_members(self) -> None:
        members = self.service.members.get_all_members()
        if not members:
            print("No members found.")
            return
        for member in members:
            outstanding = self.service.get_outstanding_fine(member.member_id, date.today())
            print(
                f"{member.member_id} | {member.name} | {member.email} | "
                f"Borrowed: {len(member.get_borrowed_books())} | Fines: ${outstanding:.2f}"
            )

    def _pay_fine(self) -> None:
        member_id = input("Member ID: ").strip()
        amount = float(input("Amount to pay: ").strip())
        try:
            paid = self.service.pay_member_fine(member_id, amount)
            print(f"Payment applied: ${paid:.2f}")
        except Exception as error:
            print(f"Could not process payment: {error}")

    def _check_out_book(self) -> None:
        member_id = input("Member ID: ").strip()
        isbn = input("ISBN: ").strip()
        date_input = input("Checkout date (YYYY-MM-DD, blank for today): ").strip()
        checkout_date = parse_date_string(date_input) if date_input else None
        success, message, loan = self.service.check_out_book(member_id, isbn, checkout_date)
        print(message)
        if success and loan is not None:
            print(f"Loan ID: {loan.loan_id}, Due date: {loan.due_date}")

    def _check_in_book(self) -> None:
        copy_id = input("Copy ID: ").strip()
        date_input = input("Return date (YYYY-MM-DD, blank for today): ").strip()
        return_date = parse_date_string(date_input) if date_input else None
        success, message, fine = self.service.check_in_book(copy_id, return_date)
        print(message)
        if success:
            print(f"Fine charged: ${fine:.2f}")

    def _reserve_book(self) -> None:
        member_id = input("Member ID: ").strip()
        copy_id = input("Copy ID: ").strip()
        success, message, reservation = self.service.reserve_book(member_id, copy_id)
        print(message)
        if success and reservation is not None:
            print(f"Reservation ID: {reservation.reservation_id}, Expires: {reservation.expires_on}")

    def _generate_overdue_notifications(self) -> None:
        messages = self.service.generate_overdue_notifications(date.today())
        if not messages:
            print("No overdue notifications generated.")
            return
        for message in messages:
            print(message)

    def _report_overdue_books(self) -> None:
        rows = self.service.report_service.list_overdue_books(date.today())
        if not rows:
            print("No overdue books.")
            return
        for row in rows:
            print(
                f"{row['copy_id']} | {row['book_title']} | {row['member_name']} | "
                f"Due: {row['due_date']} | Fine: ${row['fine']:.2f}"
            )

    def _report_most_borrowed_books(self) -> None:
        rows = self.service.report_service.most_borrowed_books()
        if not rows:
            print("No borrowing activity yet.")
            return
        for row in rows:
            print(f"{row['title']} ({row['isbn']}) - Borrowed {row['borrow_count']} times")

    def _report_members_with_fines(self) -> None:
        rows = self.service.report_service.members_with_outstanding_fines(date.today())
        if not rows:
            print("No members with outstanding fines.")
            return
        for row in rows:
            print(f"{row['member_id']} | {row['name']} | ${row['fine_total']:.2f}")

    def _report_daily_circulation(self) -> None:
        date_input = input("Date (YYYY-MM-DD, blank for today): ").strip()
        target_date = parse_date_string(date_input) if date_input else date.today()
        row = self.service.report_service.daily_circulation_report(target_date)
        print(
            f"Date: {row['date']} | Checkouts: {row['checkouts']} | Returns: {row['returns']}"
        )

    def _list_books(self, books: list) -> None:
        if not books:
            print("No books found.")
            return
        for book in books:
            print(format_book_display(book))

    def _save_and_exit(self) -> None:
        self.persistence.save(
            self.service.books,
            self.service.members,
            self.service.loans,
            self.service.reservations,
        )
        print("Data saved. Goodbye.")


if __name__ == "__main__":
    LibraryCLI().run()
