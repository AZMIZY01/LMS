"""String helper routines used by the Library Management System."""

from __future__ import annotations

from src.models.book import Book


def format_book_display(book: Book) -> str:
    """Return a human-readable description of a book."""
    return book.get_display_text()


def normalize_search_term(term: str) -> str:
    """Normalize a search term for case-insensitive comparison."""
    return term.strip().lower()


def validate_email(email: str) -> bool:
    """Perform simple email validation suitable for a course project."""
    cleaned = email.strip()
    return "@" in cleaned and "." in cleaned.split("@")[-1] and not cleaned.startswith("@")
