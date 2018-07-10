from django.db import models
from typing import Dict

from crypto.rsa import new_keys
from crypto.utils import sha512
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
    USER_TYPE_CHOICES = (
        (1, 'customer'),
        (2, 'bank'),
        (3, 'manager')
    )

    user_type = models.PositiveSmallIntegerField(choices=USER_TYPE_CHOICES)
    password = models.CharField(max_length=1000)
    username = models.CharField(max_length=100, unique=True)
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

    @property
    def model(self):
        if self.user_type == 1:
            return Customer
        if self.user_type == 2:
            return Bank
        return Manager


class Bank(models.Model):
    login = models.OneToOneField(Login, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, unique=True)
    wallet = models.ForeignKey('Wallet', on_delete=models.CASCADE, related_name='bank_wallet', null=True)

    def init(self, uname, password, name):
        self.name = name
        login = Login(user_type=2).init(uname, password)
        login.save()
        self.login = login
        return self

    def create_wallet(self):
        wallet = Wallet()
        wallet.set_keys()
        wallet.save()
        self.wallet = wallet
        return self

    def get_keys(self):
        return self.wallet.get_keys()


    def get_balance(self):
        return self.wallet.get_balanc()


class Wallet(models.Model):
    wallet_id = models.CharField(max_length=20)
    bank = models.ForeignKey(Bank, on_delete = models.CASCADE, related_name='from_bank', null=True)
    pub = models.CharField(max_length=1024)
    pv = models.CharField(max_length=1024)

    def set_keys(self):
        header_len = 27
        self.pub, self.pv = new_keys(1024)
        self.pv = self.pv.export_key().decode()
        self.pub = self.pub.export_key().decode()
        self.wallet_id = self.pub[header_len:header_len + 20]
        return self

    def get_keys(self):
        return self.pub, self.pv


    def set_bank(self, bank):
        self.bank = bank


    def get_balance(self):
        utxos = TransactionOutput.objects.filter(recipient=self.pub, spent=False)

        amount = 0

        for utxo in utxos:
            amount += utxo.value

        return amount


class Customer(models.Model):
    login = models.OneToOneField(Login, on_delete=models.CASCADE)
    wallet = models.ForeignKey(Wallet, on_delete = models.CASCADE)

    def init(self, uname, password, bank_name):
        login = Login(user_type=1).init(uname, password)
        login.save()
        self.login = login
        wallet = Wallet(bank=Bank.objects.get(name=bank_name)).set_keys()
        wallet.save()
        self.wallet = wallet
        return self


    def get_keys(self):
        return self.wallet.get_keys()


    def get_balance(self):
        return self.wallet.get_balanc()


    def get_bank():
        return self.wallet.bank


class Manager(SingletonModel):
    login = models.OneToOneField(Login, on_delete=models.CASCADE)

    def init(self, uname, password):
        login = Login(user_type=3)
        login.init(uname, password)
        login.save()
        self.login = login



class BankSettings(SingletonModel):
    transaction_count_on_block = models.IntegerField()
    fee = models.DecimalField(max_digits=24, decimal_places=4)
    reward = models.DecimalField(max_digits=24, decimal_places=4)
    difficulty = models.IntegerField()
    generate_token = models.CharField(max_length=100)
    loan_condition = models.DecimalField(max_digits=24, decimal_places=4)


