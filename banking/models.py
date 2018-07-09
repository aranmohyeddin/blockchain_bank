from crypto.utils import sha512
from django.db import models
from utils.models import SingletonModel
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


class Manager(Customer, SingletonModel):
    pass


class BankSettings(SingletonModel):
    transaction_count_on_block = models.IntegerField()
    fee = models.DecimalField(max_digits=24, decimal_places=4)
    reward = models.DecimalField(max_digits=24, decimal_places=4)
    difficulty = models.IntegerField()
    generate_token = models.CharField(max_length=100)
    loan_condition = models.DecimalField(max_digits=24, decimal_places=4)


