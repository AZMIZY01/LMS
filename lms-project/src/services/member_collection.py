# member_collection.py 
class MemberCollection: 
"""ADT for managing a collection of library members.""" 
def __init__(self): 
self._members = {}  # member_id -> Member 
def add_member(self, member): 
if member.member_id in self._members: 
raise ValueError(f"Member {member.member_id} already exists") 
self._members[member.member_id] = member 
def remove_member(self, member_id): 
if member_id not in self._members: 
raise KeyError(f"Member {member_id} not found") 
# Check if member has borrowed books 
member = self._members[member_id] 
if member.get_borrowed_books(): 
raise ValueError("Cannot remove member with borrowed books") 
del self._members[member_id] 
def find_by_id(self, member_id): 
return self._members.get(member_id) 
def find_by_name(self, name_substring): 
results = [] 
for member in self._members.values(): 
if name_substring.lower() in member.name.lower(): 
results.append(member) 
return results 
def get_all_members(self): 
return list(self._members.values()) 
def count(self): 
return len(self._members)
