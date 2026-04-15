"""Tests for book collection searching and storage."""

from __future__ import annotations

import pytest

from src.models.book import Book
from src.services.book_collection import BookCollection


class TestBookCollection:
    """Verify collection behavior for books."""

    def test_add_and_find_book(self) -> None:
        collection = BookCollection()
        book = Book("Clean Code", "Robert C. Martin", "9780132350884", 2008, "COPY-1")
        collection.add_book(book)
        assert collection.find_by_copy_id("COPY-1") == book

    def test_duplicate_copy_raises_error(self) -> None:
        collection = BookCollection()
        book = Book("Clean Code", "Robert C. Martin", "9780132350884", 2008, "COPY-1")
        collection.add_book(book)
        with pytest.raises(ValueError):
            collection.add_book(book)

    def test_search_books_by_title_and_isbn(self) -> None:
        collection = BookCollection()
        first = Book("Clean Code", "Robert C. Martin", "9780132350884", 2008, "COPY-1")
        second = Book("The Clean Coder", "Robert C. Martin", "9780137081073", 2011, "COPY-2")
        collection.add_book(first)
        collection.add_book(second)

        results = collection.search({"title": "clean code", "isbn": "9780132350884"})
        assert results[0].copy_id == "COPY-1"
        assert len(results) == 2
