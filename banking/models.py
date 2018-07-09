from crypto.utils import sha512
from django.db import models
from crypto.utils import generate_rsa_keys

from utils.models import SingletonModel
try:
    from secrets import token_hex
except ImportError:
    from os import urandom

    def token_hex(nbytes=None):
        return urandom(nbytes).hex()


class Login(models.Model):
    username = models.CharField(max_length=100)
    password = models.CharField(max_length=1000)  # this is not the actualy password it is sha512(salt + password)
    salt = models.CharField(max_length=1000)


    def init(uname, password):
        self.username = uname
        self.salt = token_hex(32)
        self.password = sha512(self.salt + password)


    def authenticate(password):
        if self.password == sha512(self.salt + password):
            return true
        return false


    class Meta:
        abstract = True


class Bank(Login):
    name = models.CharField(max_length=100)
    token = models.CharField(max_length=100)
    wallet = models.ForeignKey('Wallet', on_delete=models.CASCADE)


    def create_wallet():
        self.wallet = Wallet(bank=self)
        self.wallet.set_keys()
        self.wallet.save()
        return self


    def get_keys():
        return self.wallet.get_keys()


class Wallet(models.Model):
    wallet_id = models.CharField(max_length=20)
    bank = models.ForeignKey(Bank, on_delete = models.CASCADE)
    pub = models.CharField(max_length=1024)
    pv = models.CharField(max_length=1024)


    def set_keys():
        self.pv, self.pub = generate_rsa_keys()
        self.wallet_id = self.pub[:20]


    def get_keys():
        return self.pub, self.pv


class Customer(Login):
    wallet = models.ForeignKey(Wallet, on_delete = models.CASCADE)


    def create_wallet(bank_name):
        self.wallet = Wallet(bank=Bank.objects.get(name=bank_name))
        self.wallet.set_keys()
        self.wallet.save()
        return self


    def get_keys():
        return self.wallet.get_keys()


class Manager(Login, SingletonModel):
    pass


class BankSettings(SingletonModel):
    transaction_count_on_block = models.IntegerField()
    fee = models.DecimalField(max_digits=24, decimal_places=4)
    reward = models.DecimalField(max_digits=24, decimal_places=4)
    difficulty = models.IntegerField()
    generate_token = models.CharField(max_length=100)
    loan_condition = models.DecimalField(max_digits=24, decimal_places=4)


