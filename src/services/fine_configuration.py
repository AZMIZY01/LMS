"""Fine configuration for overdue loan calculations."""

from __future__ import annotations

from dataclasses import dataclass, field

from src.constants import FINE_RATE_TIERS, MAX_FINE_PER_LOAN


@dataclass
class FineConfiguration:
    """Store configurable fine rules."""

    rate_tiers: list[tuple[int, int, float]] = field(default_factory=lambda: FINE_RATE_TIERS.copy())
    max_fine_per_loan: float = MAX_FINE_PER_LOAN
