"""Notification service for the Library Management System.

This implementation prints messages to the console and stores a history.
In a production system, this could be replaced with email or SMS delivery.
"""

from __future__ import annotations


class NotificationService:
    """Simple notification service used by the CLI application."""

    def __init__(self) -> None:
        self._messages: list[str] = []

    def notify(self, recipient_email: str, message: str) -> None:
        """Record a notification message for later display or inspection."""
        full_message = f"To {recipient_email}: {message}"
        self._messages.append(full_message)

    def get_messages(self) -> list[str]:
        """Return notification history."""
        return self._messages.copy()
