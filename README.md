# Library Management System

A Python-based Library Management System built from the software construction guidance in the attached SWE 405 course PDF.

## Implemented Features

- Add, edit, delete, and search books
- Track multiple copies of the same title
- Register and update members
- Check out and check in books
- Automatic overdue fine calculation using a table-driven approach
- Reservation queue for checked-out books
- Overdue notifications
- Reports for overdue books, most borrowed books, outstanding fines, and daily circulation
- JSON file persistence
- Command-line interface and Streamlit web GUI
- Unit tests with `pytest`

## Architecture

The project follows the construction decisions described in the PDF:

- **Language:** Python 3.8+
- **Structure:** three-layer style using models, services, and presentation layers
- **ADT design:** collections hide internal dictionaries and expose meaningful operations
- **Testing:** `pytest`
- **Fine calculation:** configurable table-driven tiers
- **Web UI:** Streamlit

## Project Structure

```text
lms_project/
├── src/
│   ├── models/
│   ├── services/
│   ├── utils/
│   └── constants.py
├── tests/
├── docs/
├── data/
├── main.py            # CLI entry point
├── streamlit_app.py   # Web GUI entry point
├── requirements.txt
└── README.md
```

## Getting Started

1. Create and activate a virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Run the web GUI

```bash
streamlit run streamlit_app.py
```

### Run the CLI

```bash
python main.py
```

### Run tests

```bash
pytest
```

## Web GUI Overview

The Streamlit app includes:

- A dashboard with library metrics
- Book management forms
- Member registration, updates, fine payments, and history
- Loan checkout/check-in and reservation workflows
- Reporting screens for overdue books, fines, circulation, and most borrowed titles
- Automatic persistence after successful actions

## Sample Data

On first run, the application seeds a few books and members so the system can be explored immediately.

## Notes

- Data is stored in `data/library_data.json`.
- The Streamlit sidebar includes a **Reseed Sample Data** button for resetting the demo dataset.
- The system is intentionally designed for learning and maintainability rather than database-scale throughput.
