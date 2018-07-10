from django.db import models
from typing import Dict

from utils.models import SingletonModel

from blockchain import TransactionOutput, Transaction, TransactionInput
from blockchain.models import TransactionOutput

from crypto.rsa import new_keys
from crypto.utils import sha512
from Crypto.PublicKey.RSA import RsaKey

try:
    from secrets import token_hex
except ImportError:
    from os import urandom

    def token_hex(nbytes=None):
        return urandom(nbytes).hex()


class Login(models.Model):
    class Meta:
        abstract = True

    password = models.CharField(max_length=1000)
    username = models.CharField(max_length=100)
    # this is not the actualy password it is sha512(salt + password)

    salt = models.CharField(max_length=1000)

    def init(self, uname, password):
        self.username = uname
        self.salt = token_hex(32)
        self.password = sha512(self.salt + password)
        return self

    def authenticate(self, password):
        if self.password == sha512(self.salt + password):
            return True
        return False


class Bank(Login):
    name = models.CharField(max_length=100)
    token = models.CharField(max_length=100)
    wallet = models.ForeignKey('Wallet', on_delete=models.CASCADE, related_name='bank_wallet')

    def create_wallet(self):
        self.wallet = Wallet(bank=self)
        self.wallet.set_keys()
        self.wallet.save()
        return self


    def get_keys(self):
        return self.wallet.get_keys()


class Wallet(models.Model):
    wallet_id = models.CharField(max_length=20)
    bank = models.ForeignKey(Bank, on_delete = models.CASCADE, related_name='from_bank')
    pub = models.CharField(max_length=1024)
    pv = models.CharField(max_length=1024)

    self.utxos = {}

    def set_keys(self):
        self.pv, self.pub = generate_rsa_keys()
        self.wallet_id = self.pub[:20]

    def get_keys(self):
        return self.pub, self.pv

    def get_balance(self):
        utxos = TransactionOutput.objects.filter(recipient=self.pub, spent=False)

        amount = 0

        for utxo in utxos:
            amount += utxo.value

        return amount


class Customer(Login):
    wallet = models.ForeignKey(Wallet, on_delete = models.CASCADE)

    def create_wallet(self, bank_name):
        self.wallet = Wallet(bank=Bank.objects.get(name=bank_name))
        self.wallet.set_keys()
        self.wallet.save()
        return self

    def get_keys(self):
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


