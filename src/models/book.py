"""Book model for the Library Management System."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Book:
    """Represent a single physical book copy.

    Attributes:
        title: Human-readable book title.
        author: Book author name.
        isbn: Shared ISBN for a title/edition.
        publication_year: Publication year.
        copy_id: Unique library copy identifier.
        is_reference_only: Whether this copy cannot be borrowed.
        status: Current copy status.
        borrow_count: Number of times the copy has been borrowed.
    """

    title: str
    author: str
    isbn: str
    publication_year: int
    copy_id: str
    is_reference_only: bool = False
    status: str = field(default="available")
    borrow_count: int = field(default=0)

    VALID_STATUSES = {"available", "checked_out", "reserved", "lost"}

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValueError("Book title cannot be empty")
        if not self.author.strip():
            raise ValueError("Book author cannot be empty")
        if not self.isbn.strip():
            raise ValueError("ISBN cannot be empty")
        if self.publication_year <= 0:
            raise ValueError("Publication year must be positive")
        if self.status not in self.VALID_STATUSES:
            raise ValueError(f"Invalid book status: {self.status}")

    def is_available(self) -> bool:
        """Return True when the book can be checked out."""
        return self.status == "available" and not self.is_reference_only

    def can_be_reserved(self) -> bool:
        """Return True when the book can accept reservations."""
        return not self.is_reference_only and self.status in {"checked_out", "reserved"}

    def check_out(self) -> None:
        """Mark the book as checked out."""
        if not self.is_available():
            raise ValueError("Book is not available for checkout")
        self.status = "checked_out"
        self.borrow_count += 1

    def check_in(self) -> None:
        """Mark the book as available again."""
        if self.status not in {"checked_out", "reserved"}:
            raise ValueError("Book is not currently checked out or reserved")
        self.status = "available"

    def mark_reserved(self) -> None:
        """Mark the book as reserved."""
        if self.is_reference_only:
            raise ValueError("Reference books cannot be reserved")
        self.status = "reserved"

    def mark_lost(self) -> None:
        """Mark the book as lost."""
        self.status = "lost"

    def get_display_text(self) -> str:
        """Return a human-readable display string for the book."""
        return (
            f"{self.title} by {self.author} | ISBN: {self.isbn} | "
            f"Year: {self.publication_year} | Copy ID: {self.copy_id} | "
            f"Status: {self.status}"
        )
