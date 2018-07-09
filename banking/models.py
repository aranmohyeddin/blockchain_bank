from crypto.utils import sha512
from django.db import models
from crypto.utils import generate_rsa_keys

try:
    from secrets import token_hex
except ImportError:
    from os import urandom

    def token_hex(nbytes=None):
        return urandom(nbytes).hex()


class Wallet():
    wallet_id = models.CharField(max_length=20)
    bank = models.ForeignKey(Bank, on_delete = models.CASCADE)
    pub = models.CharField(max_length=1024)
    pv = models.CharField(max_length=1024)


    def __init__(self, bank):
        self.bank = bank
        self.pv, self.pub = generate_rsa_keys():
        self.wallet_id = self.pub[:20]


class Customer(models.Model):
    username = models.CharField(max_length=100)
    password = models.CharField(max_length=1000)  # this is not the actual password it is sha512(salt + password)
    salt = models.CharField(max_length=1000)
        wallet = models.OneToOneField(Wallet)

    def set_password(self, password):
        self.salt = token_hex(32)
        self.password = sha512(self.salt + password)

