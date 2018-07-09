from crypto.utils import sha512
from django.db import models

try:
    from secrets import token_hex
except ImportError:
    from os import urandom

    def token_hex(nbytes=None):
        return urandom(nbytes).hex()


class Customer(models.Model):
    username = models.CharField(max_length=100)
    password = models.CharField(max_length=1000)  # this is not the actualy password it is sha512(salt + password)
    salt = models.CharField(max_length=1000)

    def set_password(self, password):
        self.salt = token_hex(32)
        self.password = sha512(self.salt + password)

