"""Shared pytest fixtures for the LMS project."""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.services.library_service import LibraryService


@pytest.fixture
def service() -> LibraryService:
    """Return a fresh library service with seed-like test data."""
    library_service = LibraryService()
    library_service.add_book("Clean Code", "Robert C. Martin", "9780132350884", 2008, "COPY-001")
    library_service.add_book("Clean Code", "Robert C. Martin", "9780132350884", 2008, "COPY-002")
    library_service.add_book("Python Crash Course", "Eric Matthes", "9781593279288", 2019, "COPY-003")
    library_service.register_member("Alice Johnson", "MEM-001", "alice@example.com", "555-0101")
    library_service.register_member("Bob Smith", "MEM-002", "bob@example.com", "555-0102")
    return library_service


@pytest.fixture
def january_date() -> date:
    """Provide a stable reference date for tests."""
    return date(2026, 1, 15)
