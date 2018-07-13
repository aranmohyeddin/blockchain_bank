from django.db import models
from typing import Dict

from crypto.rsa import new_keys
from crypto.utils import sha512
from utils.models import SingletonModel

from crypto.rsa import new_keys
from crypto.utils import sha512
from Crypto.PublicKey.RSA import RsaKey
from Crypto.Cipher import AES
import hashlib
import base64

from blockchain.transaction import Transaction
from blockchain.transaction_input import TransactionInput
from blockchain import BlockChain

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

    def get_keys_str(self):
        return self.wallet.get_keys_str()


class Wallet(models.Model):
    wallet_id = models.CharField(max_length=20)
    bank = models.ForeignKey(Bank, on_delete = models.CASCADE, related_name='from_bank', null=True)
    pub = models.CharField(max_length=1024)
    pv = models.CharField(max_length=3000)

    def set_keys(self):
        header_len = 27
        self.pub, self.pv = new_keys(1024)
        self.pub = self.pub.export_key().decode()
        self.pv = self.pv.export_key().decode()
        salt = token_hex(8)
        key = hashlib.sha256((self.pub[:50] + 'salt' + salt).encode('utf-8')).digest()
        for i in range(10):
            key = hashlib.sha256(key + 'pepper'.encode('utf-8')).digest()
        padding_length = 32 - (len(self.pv) % 32)
        padding = chr(padding_length) * padding_length
        padded = self.pv + padding
        cipher = AES.new(key, AES.MODE_ECB).encrypt(padded.encode("utf8"))
        cipher = base64.b64encode(cipher)
        self.pv = cipher.decode('utf8') + salt
        self.wallet_id = self.pub[header_len + 39:header_len + 59]
        return self

    def get_keys(self):
        pub = ''.join(self.pub.split('\n')[1:-1])
        pv = ''.join(self.get_pv().split('\n')[1:-1])
        return pub, pv

    def get_keys_str(self):
        return self.pub, self.get_pv()

    def get_pv(self):
        salt = self.pv[-16:]
        ciphertext = self.pv[:-16]
        ciphertext = ciphertext.encode('utf8')
        ciphertext = base64.b64decode(ciphertext)
        key = hashlib.sha256((self.pub[:50] + 'salt' + salt).encode('utf8')).digest()
        for i in range(10):
            key = hashlib.sha256(key + 'pepper'.encode('utf-8')).digest()
        cipher = AES.new(key, AES.MODE_ECB)
        padded = cipher.decrypt(ciphertext)
        padding_length = padded[-1]
        return padded[:-padding_length].decode('utf8')

    def set_bank(self, bank):
        self.bank = bank

    def get_balance(self, blockchain: BlockChain):
        amount = blockchain.get_balance_for_public_key(self.get_keys()[0])
        return amount

    def send_funds(self, recipient_public_key_str: str, value: float, blockchain: BlockChain):
        transaction = blockchain.send_funds_from_to(sender_public_key_str=self.get_keys()[0],
                                                    sender_private_key_str=self.get_keys()[1],
                                                    recipient_public_key_str=recipient_public_key_str,
                                                    value=value)
        return transaction


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

    def get_keys_str(self):
        return self.wallet.get_keys_str()

    def get_bank(self):
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


