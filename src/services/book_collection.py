"""Book collection ADT for managing library books."""

from __future__ import annotations

from collections import defaultdict

from src.models.book import Book


class BookCollection:
    """ADT for managing books while hiding dictionary implementation."""

    def __init__(self) -> None:
        self._books_by_copy_id: dict[str, Book] = {}
        self._copies_by_isbn: dict[str, list[str]] = defaultdict(list)

    def add_book(self, book: Book) -> None:
        """Add a book copy to the collection."""
        if book.copy_id in self._books_by_copy_id:
            raise ValueError(f"Book copy {book.copy_id} already exists")
        self._books_by_copy_id[book.copy_id] = book
        self._copies_by_isbn[book.isbn].append(book.copy_id)

    def update_book(self, copy_id: str, **changes: object) -> Book:
        """Update a book copy with supported fields and return it."""
        book = self.find_by_copy_id(copy_id)
        if book is None:
            raise KeyError(f"Book copy {copy_id} not found")

        allowed_fields = {"title", "author", "publication_year", "is_reference_only", "status"}
        for field_name, value in changes.items():
            if field_name not in allowed_fields:
                raise ValueError(f"Unsupported field: {field_name}")
            setattr(book, field_name, value)
        return book

    def remove_book(self, copy_id: str) -> None:
        """Remove a book copy from the collection."""
        book = self._books_by_copy_id.get(copy_id)
        if book is None:
            raise KeyError(f"Book copy {copy_id} not found")
        del self._books_by_copy_id[copy_id]
        self._copies_by_isbn[book.isbn].remove(copy_id)
        if not self._copies_by_isbn[book.isbn]:
            del self._copies_by_isbn[book.isbn]

    def find_by_copy_id(self, copy_id: str) -> Book | None:
        """Find a book copy by its unique copy ID."""
        return self._books_by_copy_id.get(copy_id)

    def find_by_isbn(self, isbn: str) -> list[Book]:
        """Return all book copies with the given ISBN."""
        return [self._books_by_copy_id[copy_id] for copy_id in self._copies_by_isbn.get(isbn, [])]

    def find_available_copy_by_isbn(self, isbn: str) -> Book | None:
        """Return the first available copy for an ISBN."""
        for book in self.find_by_isbn(isbn):
            if book.is_available():
                return book
        return None

    def search(self, criteria: dict[str, object]) -> list[Book]:
        """Search books by multiple criteria and rank by relevance."""
        results: list[tuple[Book, int]] = []

        for book in self._books_by_copy_id.values():
            score = 0

            title = str(criteria.get("title", "")).strip().lower()
            if title and title in book.title.lower():
                score += 10
                if title == book.title.lower():
                    score += 5

            author = str(criteria.get("author", "")).strip().lower()
            if author and author in book.author.lower():
                score += 8
                if author == book.author.lower():
                    score += 4

            isbn = str(criteria.get("isbn", "")).strip()
            if isbn and isbn == book.isbn:
                score += 20

            year = criteria.get("year")
            if year is not None and year != "" and int(year) == book.publication_year:
                score += 5

            if score > 0:
                results.append((book, score))

        results.sort(key=lambda item: (-item[1], item[0].title, item[0].copy_id))
        return [book for book, _ in results]

    def get_all_books(self) -> list[Book]:
        """Return all books as a defensive list copy."""
        return list(self._books_by_copy_id.values())

    def count(self) -> int:
        """Return the number of book copies."""
        return len(self._books_by_copy_id)
