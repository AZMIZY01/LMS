# LMS Architecture Overview

## Domain Models

- `Book`: a single physical book copy
- `Member`: a library member and borrowing state
- `LoanRecord`: one checkout transaction
- `Reservation`: one reservation request

## ADT-Style Collections

- `BookCollection`
- `MemberCollection`
- `LoanCollection`
- `ReservationCollection`

These classes hide dictionary-based storage and expose stable operations like add, remove, search, and find.

## Business Services

- `LibraryService`: orchestrates book, member, loan, and reservation workflows
- `FineCalculator`: computes overdue fines with configurable tiers
- `PersistenceService`: saves and loads state from JSON
- `ReportService`: generates operational reports
- `NotificationService`: records notification messages

## Utilities

- `date_helpers.py`
- `string_helpers.py`

## Construction Choices Reflected from the PDF

- Encapsulation through collection classes and model methods
- Clear routine names and small focused methods
- Table-driven fine calculation
- Command-line menu system with structured control flow
- Unit tests around core business logic
