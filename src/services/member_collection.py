"""Member collection ADT for managing library members."""

from __future__ import annotations

from src.models.member import Member


class MemberCollection:
    """ADT for managing members while hiding dictionary implementation."""

    def __init__(self) -> None:
        self._members: dict[str, Member] = {}

    def add_member(self, member: Member) -> None:
        """Add a member to the collection."""
        if member.member_id in self._members:
            raise ValueError(f"Member {member.member_id} already exists")
        self._members[member.member_id] = member

    def remove_member(self, member_id: str) -> None:
        """Remove a member if they have no active loans."""
        member = self._members.get(member_id)
        if member is None:
            raise KeyError(f"Member {member_id} not found")
        if member.get_borrowed_books():
            raise ValueError("Cannot remove member with borrowed books")
        del self._members[member_id]

    def find_by_id(self, member_id: str) -> Member | None:
        """Find a member by ID."""
        return self._members.get(member_id)

    def find_by_name(self, name_substring: str) -> list[Member]:
        """Find members whose names contain the given substring."""
        search_term = name_substring.strip().lower()
        if not search_term:
            return self.get_all_members()
        return [
            member
            for member in self._members.values()
            if search_term in member.name.lower()
        ]

    def get_all_members(self) -> list[Member]:
        """Return all members as a defensive list copy."""
        return list(self._members.values())

    def count(self) -> int:
        """Return the number of members."""
        return len(self._members)
