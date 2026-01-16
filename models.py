from flask_login import UserMixin

class AuthUser(UserMixin):
    def __init__(self, id, email, first_name, last_name, role):
        self.id = id
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.role = role

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"