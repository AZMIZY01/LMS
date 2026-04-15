"""Project-wide constants for the Library Management System."""

MAX_BORROW_LIMIT = 5
DEFAULT_LOAN_PERIOD_DAYS = 14
RESERVATION_EXPIRY_DAYS = 7
MAX_FINE_BEFORE_SUSPENSION = 50.00
PERSISTENCE_FILE = "data/library_data.json"
DATE_FORMAT = "%Y-%m-%d"
CURRENCY_SYMBOL = "₦"

# Fine tiers are incremental: (inclusive_start_day, inclusive_end_day, rate_per_day)
FINE_RATE_TIERS = [
    (1, 7, 0.50),
    (8, 30, 1.00),
    (31, 3650, 2.00),
]
MAX_FINE_PER_LOAN = 100.00
