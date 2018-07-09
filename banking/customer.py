from crypto.utils import sha512
from secrets import token_hex

class Customer:

    id = None;
    password = None; # this is not the actualy password it is sha512(salt + password)
    salt = None;

    def __init__(self, id, password):
        self.id = id
        self.salt = token_hex(32)
        self.password = sha512(self.salt + passowrd)

