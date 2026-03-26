# member.py 
class Member: 
    """Represents a library member.""" 
     
    def __init__(self, name, member_id, email): 
        self._name = name 
        self._member_id = member_id 
        self._email = email 
        self._borrowed_books = [] 
        self._fines_owed = 0.0 
     
    # Properties for controlled access 
    @property 
    def name(self): 
        return self._name 
     
    @property 
    def member_id(self): 
        return self._member_id 
     
    def borrow_book(self, book): 
        """Borrow a book if within limits.""" 
        if len(self._borrowed_books) >= 5: 
            return False 
        self._borrowed_books.append(book) 
        return True 
     
    def return_book(self, book): 
        """Return a borrowed book.""" 
        if book in self._borrowed_books: 
            self._borrowed_books.remove(book) 
            return True 
        return False 
     
    def get_borrowed_books(self): 
        """Return a copy of the borrowed books list.""" 
        return self._borrowed_books.copy() 
     
    def add_fine(self, amount): 
        """Add a fine to the member's account.""" 
        self._fines_owed += amount 
     
    def pay_fine(self, amount): 
        """Pay part or all of fines owed.""" 
        if amount > self._fines_owed: 
            amount = self._fines_owed 
        self._fines_owed -= amount 
        return amount 
     
def get_fines_owed(self): 
return self._fines_owed
