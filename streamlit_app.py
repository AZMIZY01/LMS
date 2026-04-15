"""Streamlit web interface for the Library Management System."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import streamlit as st

from src.constants import CURRENCY_SYMBOL, PERSISTENCE_FILE
from src.services.library_service import LibraryService
from src.services.persistence_service import PersistenceService
from src.utils.date_helpers import parse_date_string


st.set_page_config(
    page_title="Library Management System",
    page_icon="📚",
    layout="wide",
)


PROJECT_ROOT = Path(__file__).resolve().parent
DATA_PATH = PROJECT_ROOT / PERSISTENCE_FILE


def load_service() -> tuple[LibraryService, PersistenceService]:
    """Load the persisted library state and return ready-to-use services."""
    persistence = PersistenceService(str(DATA_PATH))
    books, members, loans, reservations = persistence.load()
    service = LibraryService(books=books, members=members, loans=loans, reservations=reservations)
    if service.books.count() == 0 and service.members.count() == 0:
        service.seed_sample_data()
        persistence.save(service.books, service.members, service.loans, service.reservations)
    return service, persistence


def save_service(service: LibraryService, persistence: PersistenceService) -> None:
    """Persist the current library state to disk."""
    persistence.save(service.books, service.members, service.loans, service.reservations)


def set_flash(message: str, level: str = "success") -> None:
    """Store a one-time status message across Streamlit reruns."""
    st.session_state["flash_message"] = message
    st.session_state["flash_level"] = level


def show_flash() -> None:
    """Render and clear any stored flash message."""
    message = st.session_state.pop("flash_message", None)
    level = st.session_state.pop("flash_level", "success")
    if not message:
        return
    if level == "success":
        st.success(message)
    elif level == "warning":
        st.warning(message)
    elif level == "info":
        st.info(message)
    else:
        st.error(message)



def format_currency(amount: float) -> str:
    """Format currency values consistently for the UI."""
    return f"{CURRENCY_SYMBOL}{amount:,.2f}"

def book_rows(service: LibraryService) -> list[dict[str, object]]:
    """Return book data formatted for tables."""
    rows = []
    for book in sorted(service.books.get_all_books(), key=lambda item: (item.title, item.copy_id)):
        rows.append(
            {
                "Title": book.title,
                "Author": book.author,
                "ISBN": book.isbn,
                "Year": book.publication_year,
                "Copy ID": book.copy_id,
                "Status": book.status,
                "Reference Only": "Yes" if book.is_reference_only else "No",
                "Borrow Count": book.borrow_count,
            }
        )
    return rows


def member_rows(service: LibraryService) -> list[dict[str, object]]:
    """Return member data formatted for tables."""
    rows = []
    for member in sorted(service.members.get_all_members(), key=lambda item: item.member_id):
        rows.append(
            {
                "Member ID": member.member_id,
                "Name": member.name,
                "Email": member.email,
                "Phone": member.phone,
                "Active": "Yes" if member.is_active else "No",
                "Borrowed Copies": len(member.get_borrowed_books()),
                "Stored Fines": format_currency(member.fines_owed),
                "Borrowed Copy IDs": ", ".join(member.get_borrowed_books()) or "—",
            }
        )
    return rows


def active_loan_rows(service: LibraryService) -> list[dict[str, object]]:
    """Return active loan data formatted for tables."""
    rows = []
    for loan in service.loans.get_all_loans():
        if not loan.is_active():
            continue
        book = service.books.find_by_copy_id(loan.copy_id)
        member = service.members.find_by_id(loan.member_id)
        rows.append(
            {
                "Loan ID": loan.loan_id,
                "Copy ID": loan.copy_id,
                "Book": book.title if book else loan.copy_id,
                "Member": member.name if member else loan.member_id,
                "Member ID": loan.member_id,
                "Checkout Date": loan.checkout_date.isoformat(),
                "Due Date": loan.due_date.isoformat(),
                "Overdue": "Yes" if loan.is_overdue(date.today()) else "No",
            }
        )
    rows.sort(key=lambda item: (item["Due Date"], item["Loan ID"]))
    return rows


def reservation_rows(service: LibraryService) -> list[dict[str, object]]:
    """Return reservation data formatted for tables."""
    rows = []
    today = date.today()
    for reservation in service.reservations.get_all_reservations():
        book = service.books.find_by_copy_id(reservation.copy_id)
        member = service.members.find_by_id(reservation.member_id)
        rows.append(
            {
                "Reservation ID": reservation.reservation_id,
                "Copy ID": reservation.copy_id,
                "Book": book.title if book else reservation.copy_id,
                "Member": member.name if member else reservation.member_id,
                "Reserved On": reservation.reserved_on.isoformat(),
                "Expires On": reservation.expires_on.isoformat(),
                "Status": "Active" if reservation.is_active(today) else "Expired",
            }
        )
    rows.sort(key=lambda item: (item["Status"], item["Expires On"], item["Reservation ID"]))
    return rows


def render_dashboard(service: LibraryService) -> None:
    """Render a high-level system overview."""
    st.header("Dashboard")
    today = date.today()
    active_loans = active_loan_rows(service)
    overdue_books = service.report_service.list_overdue_books(today)
    fine_rows = service.report_service.members_with_outstanding_fines(today)
    reservations = reservation_rows(service)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Books", service.books.count())
    col2.metric("Members", service.members.count())
    col3.metric("Active Loans", len(active_loans))
    col4.metric("Reservations", len([row for row in reservations if row["Status"] == "Active"]))

    col5, col6 = st.columns(2)
    total_fines = sum(float(row["fine_total"]) for row in fine_rows)
    col5.metric("Overdue Loans", len(overdue_books))
    col6.metric("Outstanding Fines", format_currency(total_fines))

    left, right = st.columns(2)
    with left:
        st.subheader("Active Loans")
        if active_loans:
            st.dataframe(active_loans, use_container_width=True, hide_index=True)
        else:
            st.info("No active loans.")
    with right:
        st.subheader("Members With Fines")
        if fine_rows:
            display_rows = [
                {
                    "Member ID": row["member_id"],
                    "Name": row["name"],
                    "Fine Total": format_currency(float(row["fine_total"])),
                }
                for row in fine_rows
            ]
            st.dataframe(display_rows, use_container_width=True, hide_index=True)
        else:
            st.info("No outstanding fines.")


def render_books(service: LibraryService, persistence: PersistenceService) -> None:
    """Render all book management features."""
    st.header("Book Management")

    tab_add, tab_edit, tab_delete, tab_search, tab_all = st.tabs(
        ["Add Book", "Edit Book", "Delete Book", "Search Books", "All Books"]
    )

    with tab_add:
        with st.form("add_book_form"):
            col1, col2 = st.columns(2)
            title = col1.text_input("Title")
            author = col2.text_input("Author")
            isbn = col1.text_input("ISBN")
            publication_year = col2.number_input("Publication Year", min_value=1, step=1, value=2024)
            copy_id = col1.text_input("Copy ID")
            is_reference_only = col2.checkbox("Reference only")
            submitted = st.form_submit_button("Add Book")

        if submitted:
            try:
                service.add_book(
                    title=title,
                    author=author,
                    isbn=isbn,
                    publication_year=int(publication_year),
                    copy_id=copy_id,
                    is_reference_only=is_reference_only,
                )
                save_service(service, persistence)
                set_flash(f"Book '{title}' added successfully.")
                st.rerun()
            except Exception as error:  # pragma: no cover - UI path
                st.error(str(error))

    with tab_edit:
        books = sorted(service.books.get_all_books(), key=lambda item: (item.title, item.copy_id))
        if not books:
            st.info("No books available to edit.")
        else:
            selected_copy_id = st.selectbox(
                "Select a book copy",
                options=[book.copy_id for book in books],
                format_func=lambda copy_id: next(
                    f"{book.title} ({book.copy_id})" for book in books if book.copy_id == copy_id
                ),
                key="edit_book_copy_id",
            )
            selected_book = service.books.find_by_copy_id(selected_copy_id)
            if selected_book is not None:
                st.caption(
                    f"Current details: {selected_book.title} by {selected_book.author} | "
                    f"ISBN {selected_book.isbn} | Status {selected_book.status}"
                )
                with st.form("edit_book_form"):
                    new_title = st.text_input("New title", placeholder=selected_book.title)
                    new_author = st.text_input("New author", placeholder=selected_book.author)
                    new_year = st.number_input(
                        "New publication year",
                        min_value=1,
                        step=1,
                        value=int(selected_book.publication_year),
                    )
                    new_reference = st.checkbox(
                        "Reference only",
                        value=selected_book.is_reference_only,
                    )
                    submitted = st.form_submit_button("Update Book")

                if submitted:
                    try:
                        changes = {
                            "title": new_title.strip() or selected_book.title,
                            "author": new_author.strip() or selected_book.author,
                            "publication_year": int(new_year),
                            "is_reference_only": new_reference,
                        }
                        service.edit_book(selected_copy_id, **changes)
                        save_service(service, persistence)
                        set_flash(f"Book copy {selected_copy_id} updated.")
                        st.rerun()
                    except Exception as error:  # pragma: no cover - UI path
                        st.error(str(error))

    with tab_delete:
        books = sorted(service.books.get_all_books(), key=lambda item: (item.title, item.copy_id))
        if not books:
            st.info("No books available to delete.")
        else:
            copy_id_to_delete = st.selectbox(
                "Select a book copy to delete",
                options=[book.copy_id for book in books],
                format_func=lambda copy_id: next(
                    f"{book.title} ({book.copy_id})" for book in books if book.copy_id == copy_id
                ),
                key="delete_book_copy_id",
            )
            if st.button("Delete Selected Book", type="primary"):
                try:
                    service.delete_book(copy_id_to_delete)
                    save_service(service, persistence)
                    set_flash(f"Book copy {copy_id_to_delete} deleted.")
                    st.rerun()
                except Exception as error:  # pragma: no cover - UI path
                    st.error(str(error))

    with tab_search:
        with st.form("search_books_form"):
            col1, col2 = st.columns(2)
            title = col1.text_input("Title contains")
            author = col2.text_input("Author contains")
            isbn = col1.text_input("ISBN")
            year = col2.text_input("Year")
            submitted = st.form_submit_button("Search")

        if submitted:
            criteria = {"title": title, "author": author, "isbn": isbn, "year": year or None}
            results = service.search_books(criteria)
            if results:
                rows = [
                    {
                        "Title": book.title,
                        "Author": book.author,
                        "ISBN": book.isbn,
                        "Year": book.publication_year,
                        "Copy ID": book.copy_id,
                        "Status": book.status,
                    }
                    for book in results
                ]
                st.dataframe(rows, use_container_width=True, hide_index=True)
            else:
                st.info("No books matched the search criteria.")

    with tab_all:
        rows = book_rows(service)
        if rows:
            st.dataframe(rows, use_container_width=True, hide_index=True)
        else:
            st.info("No books in the catalog yet.")


def render_members(service: LibraryService, persistence: PersistenceService) -> None:
    """Render all member management features."""
    st.header("Member Management")
    tab_register, tab_update, tab_fines, tab_history, tab_all = st.tabs(
        [
            "Register Member",
            "Update Member",
            "Pay Fine",
            "Borrowing History",
            "All Members",
        ]
    )

    with tab_register:
        with st.form("register_member_form"):
            col1, col2 = st.columns(2)
            name = col1.text_input("Name")
            member_id = col2.text_input("Member ID")
            email = col1.text_input("Email")
            phone = col2.text_input("Phone")
            submitted = st.form_submit_button("Register Member")

        if submitted:
            try:
                service.register_member(name=name, member_id=member_id, email=email, phone=phone)
                save_service(service, persistence)
                set_flash(f"Member '{name}' registered successfully.")
                st.rerun()
            except Exception as error:  # pragma: no cover - UI path
                st.error(str(error))

    with tab_update:
        members = sorted(service.members.get_all_members(), key=lambda item: item.member_id)
        if not members:
            st.info("No members available to update.")
        else:
            selected_member_id = st.selectbox(
                "Select a member",
                options=[member.member_id for member in members],
                format_func=lambda member_id: next(
                    f"{member.name} ({member.member_id})"
                    for member in members
                    if member.member_id == member_id
                ),
            )
            member = service.members.find_by_id(selected_member_id)
            if member is not None:
                with st.form("update_member_form"):
                    new_name = st.text_input("Name", value=member.name)
                    new_email = st.text_input("Email", value=member.email)
                    new_phone = st.text_input("Phone", value=member.phone)
                    is_active = st.checkbox("Active", value=member.is_active)
                    submitted = st.form_submit_button("Update Member")

                if submitted:
                    try:
                        service.update_member(
                            selected_member_id,
                            name=new_name,
                            email=new_email,
                            phone=new_phone,
                            is_active=is_active,
                        )
                        save_service(service, persistence)
                        set_flash(f"Member {selected_member_id} updated.")
                        st.rerun()
                    except Exception as error:  # pragma: no cover - UI path
                        st.error(str(error))

    with tab_fines:
        members = sorted(service.members.get_all_members(), key=lambda item: item.member_id)
        if not members:
            st.info("No members available.")
        else:
            selected_member_id = st.selectbox(
                "Select a member to pay a fine",
                options=[member.member_id for member in members],
                format_func=lambda member_id: next(
                    f"{member.name} ({member.member_id})"
                    for member in members
                    if member.member_id == member_id
                ),
                key="pay_fine_member",
            )
            member = service.members.find_by_id(selected_member_id)
            if member is not None:
                outstanding = service.get_outstanding_fine(selected_member_id)
                st.write(f"Current total due: **{format_currency(outstanding)}**")
                with st.form("pay_fine_form"):
                    amount = st.number_input("Payment amount", min_value=0.0, step=1.0, format="%.2f")
                    submitted = st.form_submit_button("Apply Payment")
                if submitted:
                    try:
                        paid = service.pay_member_fine(selected_member_id, float(amount))
                        save_service(service, persistence)
                        set_flash(f"Payment applied: {format_currency(paid)} for member {selected_member_id}.")
                        st.rerun()
                    except Exception as error:  # pragma: no cover - UI path
                        st.error(str(error))

    with tab_history:
        members = sorted(service.members.get_all_members(), key=lambda item: item.member_id)
        if not members:
            st.info("No members available.")
        else:
            selected_member_id = st.selectbox(
                "Select a member to view history",
                options=[member.member_id for member in members],
                format_func=lambda member_id: next(
                    f"{member.name} ({member.member_id})"
                    for member in members
                    if member.member_id == member_id
                ),
                key="history_member",
            )
            try:
                history = service.get_member_borrowing_history(selected_member_id)
                rows = []
                for loan in history:
                    book = service.books.find_by_copy_id(loan.copy_id)
                    rows.append(
                        {
                            "Loan ID": loan.loan_id,
                            "Copy ID": loan.copy_id,
                            "Book": book.title if book else loan.copy_id,
                            "Checkout Date": loan.checkout_date.isoformat(),
                            "Due Date": loan.due_date.isoformat(),
                            "Return Date": loan.return_date.isoformat() if loan.return_date else "Active",
                        }
                    )
                if rows:
                    st.dataframe(rows, use_container_width=True, hide_index=True)
                else:
                    st.info("This member has no borrowing history yet.")
            except Exception as error:  # pragma: no cover - UI path
                st.error(str(error))

    with tab_all:
        rows = member_rows(service)
        if rows:
            st.dataframe(rows, use_container_width=True, hide_index=True)
        else:
            st.info("No registered members yet.")


def render_loans(service: LibraryService, persistence: PersistenceService) -> None:
    """Render checkout, return, reservation, and notification flows."""
    st.header("Loan Management")
    tab_checkout, tab_return, tab_reserve, tab_notify, tab_active, tab_reservations = st.tabs(
        [
            "Check Out",
            "Check In",
            "Reserve Book",
            "Overdue Notices",
            "Active Loans",
            "Reservations",
        ]
    )

    with tab_checkout:
        members = sorted(service.members.get_all_members(), key=lambda item: item.member_id)
        isbns = sorted({book.isbn for book in service.books.get_all_books()})
        if not members or not isbns:
            st.info("You need at least one member and one book to create a loan.")
        else:
            with st.form("checkout_form"):
                member_id = st.selectbox(
                    "Member",
                    options=[member.member_id for member in members],
                    format_func=lambda selected: next(
                        f"{member.name} ({member.member_id})"
                        for member in members
                        if member.member_id == selected
                    ),
                )
                isbn = st.selectbox("ISBN", options=isbns)
                checkout_date_value = st.date_input("Checkout date", value=date.today())
                submitted = st.form_submit_button("Check Out Book")
            if submitted:
                success, message, loan = service.check_out_book(
                    member_id=member_id,
                    isbn=isbn,
                    checkout_date=checkout_date_value,
                )
                if success:
                    save_service(service, persistence)
                    set_flash(f"{message}. Loan ID: {loan.loan_id if loan else 'N/A'}")
                    st.rerun()
                else:
                    st.error(message)

    with tab_return:
        active_loans = [loan for loan in service.loans.get_all_loans() if loan.is_active()]
        if not active_loans:
            st.info("There are no active loans to return.")
        else:
            with st.form("return_form"):
                copy_id = st.selectbox(
                    "Book copy to check in",
                    options=[loan.copy_id for loan in active_loans],
                    format_func=lambda selected_copy_id: (
                        lambda book, loan: f"{book.title if book else selected_copy_id} "
                        f"({selected_copy_id}) — borrowed by {loan.member_id}"
                    )(
                        service.books.find_by_copy_id(selected_copy_id),
                        next(loan for loan in active_loans if loan.copy_id == selected_copy_id),
                    ),
                )
                return_date_value = st.date_input("Return date", value=date.today())
                submitted = st.form_submit_button("Check In Book")
            if submitted:
                success, message, fine = service.check_in_book(copy_id=copy_id, return_date=return_date_value)
                if success:
                    save_service(service, persistence)
                    set_flash(f"{message}. Fine applied: {format_currency(fine)}")
                    st.rerun()
                else:
                    st.error(message)

    with tab_reserve:
        members = sorted(service.members.get_all_members(), key=lambda item: item.member_id)
        reservable_books = [book for book in service.books.get_all_books() if book.can_be_reserved()]
        if not members or not reservable_books:
            st.info("Reservations are available only for checked-out or already reserved non-reference books.")
        else:
            with st.form("reserve_form"):
                member_id = st.selectbox(
                    "Member",
                    options=[member.member_id for member in members],
                    format_func=lambda selected: next(
                        f"{member.name} ({member.member_id})"
                        for member in members
                        if member.member_id == selected
                    ),
                    key="reserve_member_id",
                )
                copy_id = st.selectbox(
                    "Book copy",
                    options=[book.copy_id for book in reservable_books],
                    format_func=lambda selected: next(
                        f"{book.title} ({book.copy_id})"
                        for book in reservable_books
                        if book.copy_id == selected
                    ),
                )
                reservation_date_value = st.date_input("Reservation date", value=date.today())
                submitted = st.form_submit_button("Reserve Book")
            if submitted:
                success, message, reservation = service.reserve_book(
                    member_id=member_id,
                    copy_id=copy_id,
                    reservation_date=reservation_date_value,
                )
                if success:
                    save_service(service, persistence)
                    reservation_id = reservation.reservation_id if reservation else "N/A"
                    set_flash(f"{message}. Reservation ID: {reservation_id}")
                    st.rerun()
                else:
                    st.error(message)

    with tab_notify:
        st.write("Generate overdue notifications based on a specific date.")
        notification_date = st.date_input("Notification date", value=date.today(), key="notify_date")
        if st.button("Generate Overdue Notifications"):
            messages = service.generate_overdue_notifications(notification_date)
            save_service(service, persistence)
            if messages:
                st.success(f"Generated {len(messages)} overdue notice(s).")
                for message in messages:
                    st.write(f"- {message}")
            else:
                st.info("No overdue notifications were generated.")

    with tab_active:
        rows = active_loan_rows(service)
        if rows:
            st.dataframe(rows, use_container_width=True, hide_index=True)
        else:
            st.info("No active loans.")

    with tab_reservations:
        rows = reservation_rows(service)
        if rows:
            st.dataframe(rows, use_container_width=True, hide_index=True)
        else:
            st.info("No reservations found.")


def render_reports(service: LibraryService) -> None:
    """Render reporting views."""
    st.header("Reports")
    tab_overdue, tab_popular, tab_fines, tab_daily = st.tabs(
        [
            "Overdue Books",
            "Most Borrowed Books",
            "Outstanding Fines",
            "Daily Circulation",
        ]
    )

    with tab_overdue:
        report_date = st.date_input("As of date", value=date.today(), key="overdue_report_date")
        rows = service.report_service.list_overdue_books(report_date)
        if rows:
            display_rows = [
                {
                    "Loan ID": row["loan_id"],
                    "Book": row["book_title"],
                    "Copy ID": row["copy_id"],
                    "Member": row["member_name"],
                    "Days Overdue": row["days_overdue"],
                    "Estimated Fine": format_currency(float(row["fine"])),
                }
                for row in rows
            ]
            st.dataframe(display_rows, use_container_width=True, hide_index=True)
        else:
            st.info("No overdue books for the selected date.")

    with tab_popular:
        top_n = st.slider("Number of titles", min_value=1, max_value=20, value=5)
        rows = service.report_service.most_borrowed_books(top_n=top_n)
        if rows:
            display_rows = [
                {
                    "ISBN": row["isbn"],
                    "Title": row["title"],
                    "Borrow Count": row["borrow_count"],
                }
                for row in rows
            ]
            st.dataframe(display_rows, use_container_width=True, hide_index=True)
        else:
            st.info("No borrowing activity recorded yet.")

    with tab_fines:
        report_date = st.date_input("Fine report date", value=date.today(), key="fine_report_date")
        rows = service.report_service.members_with_outstanding_fines(report_date)
        if rows:
            display_rows = [
                {
                    "Member ID": row["member_id"],
                    "Name": row["name"],
                    "Fine Total": format_currency(float(row["fine_total"])),
                }
                for row in rows
            ]
            st.dataframe(display_rows, use_container_width=True, hide_index=True)
        else:
            st.info("No outstanding fines for the selected date.")

    with tab_daily:
        report_date = st.date_input("Circulation date", value=date.today(), key="circulation_report_date")
        report = service.report_service.daily_circulation_report(report_date)
        col1, col2 = st.columns(2)
        col1.metric("Checkouts", report["checkouts"])
        col2.metric("Returns", report["returns"])

        if report["checkouts"] == 0 and report["returns"] == 0:
            st.info("No circulation activity for the selected date.")
        else:
            st.dataframe(
                [
                    {
                        "Date": report["date"],
                        "Checkouts": report["checkouts"],
                        "Returns": report["returns"],
                    }
                ],
                use_container_width=True,
                hide_index=True,
            )


def render_sidebar(service: LibraryService, persistence: PersistenceService) -> str:
    """Render sidebar navigation and utility actions."""
    with st.sidebar:
        st.title("📚 LMS Web App")
        st.caption("Streamlit interface for the Library Management System")
        page = st.radio(
            "Go to",
            options=["Dashboard", "Books", "Members", "Loans", "Reports"],
        )

        st.divider()
        st.write("**Data file**")
        st.code(str(DATA_PATH.relative_to(PROJECT_ROOT)))
        st.caption("Changes are saved automatically after successful actions.")

        st.divider()
        if st.button("Reseed Sample Data"):
            DATA_PATH.unlink(missing_ok=True)
            fresh_service, fresh_persistence = load_service()
            save_service(fresh_service, fresh_persistence)
            set_flash("Sample data reloaded.", "info")
            st.rerun()

        st.write("**Quick stats**")
        st.write(f"Books: {service.books.count()}")
        st.write(f"Members: {service.members.count()}")
        st.write(f"Loans: {len(service.loans.get_all_loans())}")
        st.write(f"Reservations: {len(service.reservations.get_all_reservations())}")
    return page


def main() -> None:
    """Run the Streamlit application."""
    service, persistence = load_service()

    st.title("Library Management System")
    st.write(
        "Manage books, members, loans, reservations, fines, and reports from a web interface."
    )
    show_flash()

    page = render_sidebar(service, persistence)

    if page == "Dashboard":
        render_dashboard(service)
    elif page == "Books":
        render_books(service, persistence)
    elif page == "Members":
        render_members(service, persistence)
    elif page == "Loans":
        render_loans(service, persistence)
    else:
        render_reports(service)


if __name__ == "__main__":
    main()
