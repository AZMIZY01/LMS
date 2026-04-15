"""Date helper routines used by the Library Management System."""

from __future__ import annotations

from datetime import date, datetime, timedelta

from src.constants import DATE_FORMAT


def calculate_due_date(checkout_date: date, loan_period_days: int) -> date:
    """Calculate a due date by adding the loan period to the checkout date."""
    return checkout_date + timedelta(days=loan_period_days)


def days_between(start_date: date, end_date: date) -> int:
    """Return the whole number of days between two dates."""
    return (end_date - start_date).days


def is_date_in_past(candidate_date: date, reference_date: date | None = None) -> bool:
    """Return True when the candidate date is earlier than the reference date."""
    comparison_date = reference_date or date.today()
    return candidate_date < comparison_date


def format_date_for_display(value: date | None) -> str:
    """Return a display-friendly string for a date."""
    return value.strftime(DATE_FORMAT) if value is not None else "N/A"


def parse_date_string(raw_value: str) -> date:
    """Parse a date string in YYYY-MM-DD format."""
    return datetime.strptime(raw_value.strip(), DATE_FORMAT).date()
