from crypto.utils import sha512
from django.db import models
from crypto.utils import generate_rsa_keys

try:
    from secrets import token_hex
except ImportError:
    from os import urandom

    def token_hex(nbytes=None):
        return urandom(nbytes).hex()

class Bank(Customer):
    name = models.CharField(max_length=100)
    token = model.CharField(max_length=100)


class Wallet(models.Model):
    wallet_id = models.CharField(max_length=20)
    bank = models.ForeignKey(Bank, on_delete = models.CASCADE)
    pub = models.CharField(max_length=1024)
    pv = models.CharField(max_length=1024)


    def set_keys():
        self.pv, self.pub = generate_rsa_keys():
        self.wallet_id = self.pub[:20]


    def get_keys():
        return self.pub, self.pv


class Customer(models.Model):
    username = models.CharField(max_length=100)
    password = models.CharField(max_length=1000)  # this is not the actual password it is sha512(salt + password)
    salt = models.CharField(max_length=64)
    wallet = models.OneToOneField(Wallet, on_delete=models.CASCADE, primary_key=True)


    def init(uname, password, bank_name):
        self.username = uname
        self.salt = token_hex(32)
        self.password = sha512(self.salt + password)
        self.wallet = Wallet(bank=Bank.objects.get(name=bank_name))
        self.wallet.set_keys()
        self.wallet.save()
        return self


    def get_keys():
        return self.wallet.get_keys()

