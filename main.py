from blockchain import Block, BlockChain, Wallet, Transaction
from typing import Dict
from blockchain import TransactionOutput
from blockchain.genesis import get_genesis_transaction

import psycopg2
import cmd, sys #cmd is used for making a repl.

# Django specific settings
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

# Ensure settings are read
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

# Your application specific imports
from banking.models import Customer


class Shell_interface(cmd.Cmd):
    intro = 'Welcome to the international banks blockchain shell.\n\
            Type help or ? to list commands.\n'
    prompt = '(bch_bank)$ '
    file = None

    def do_1(self, arg):
        '    Create the acount for the manager of all banking systems:\n\
                Create Manager "ManagerUserName" "Password"'
        print(*arg.split())

    def do_2(self, arg):
        '    :\n\
             '

    def do_3(self, arg):
        '    Show your Public Key and private Key:\n\
                3'

    def do_4(self, arg):
        '    Register a new bank:\n\
                4 "BankUserName" "Password" "Bank Name" "Token"'
        print("bank_wallet_ID")


    def do_5(self, arg):
        '    Register a new Customer to a bank:\n\
                5 "CustomerUserName" "Password" "Bank Name"'
        print("user_wallet_ID")


    def do_6(self, arg):
        '    Login:\n\
                6 "UserName" "Password"'

    def do_7(self, arg):
        '    Get Balance:\n\
                7'
        print("wallet_balance")


    def do_8(self, arg):
        '    Transfer some money to a wallet:\n\
                8 x$ to "wallet_ID"'
        print("are you sure you want to transfer x to?")
        print("you don't have enough balance")


    def do_9(self, arg):
        '    Send transaction:\n\
                9 x$ "PublicKey" "PrivateKey" to "publickey"'


    def do_10(self, arg):
        '    Request for loan from bank:\n\
                10 x$ from "Bank Name"'


    def do_11(self, arg):
        '    Show transaction history(both incoming and outgoing):\n\
                11'
        history = []
        for trans in history:
            print("\
            Sender public Key: {}\
            Receiver public key: {}\
            Amount transfered: {}\
            Transaction fee: {}\
            Transaction time: {}\
            ".format(\
            trans.sender_pub, \
            trans.receiver_pub, \
            trans.amount, \
            trans.fee, \
            trans.time_taken \
            ))

    def do_12(self, arg):# access management
        '    Show BlockChain(manager only):\n\
                12'

    def do_13(self, arg):# access management
        '    Show BlockChain balance(manager only):\n\
                13'

    def do_14(self, arg):# access management
        '    Show Invalid transactons(manager can view all, each bank can view the ones within their own network):\n\
                14'

    def do_15(self, arg):# access management
        '    Show Customers(manager can view all, each bank can view the ones within their own network):\n\
                15'

    def do_16(self, arg):
        '    Logout:\n\
                16'
        help()

    def do_quit(self, arg):
        '    Quit the Shell:\n\
                quit'
        print('Thank you for using the blockchain bank system')
        return True


if __name__ == '__main__':
    try:
        pass
        # connection = psycopg2.connect("\
        #         dbname='blockchain_bank' \
        #         user='dns' \
        #         host='localhost' \
        #         password='123qwe123' \
        #         ")
        # cursor = connection.cursor()
        # cursor.execute("""CREATE TABLE banks (name char(40));""")
        # cursor.execute("""SELECT * from banks""")
        # rows = cursor.fetchall()
        # print(rows)

        # c = Customer(username='gholi')
        # c.set_password('1234')
        # c.save()

        # c = Customer.objects.get(username='gholi')
        # print(c.pk)
        # print(c.username)
        # print(c.password)
        # print(c.salt)
    except Exception as e:
        print("can not connect to db\n", e)
    Shell_interface().cmdloop()



"""
    # a dictionary tracking unspent transaction outputs
    utxos = {}  # type: Dict[str, TransactionOutput]
    minimum_transaction = 0.1
    difficulty = 2

    blockchain = BlockChain(difficulty)

    wallet_one = Wallet(utxos)
    wallet_two = Wallet(utxos)

    wallet_coinbase = Wallet(utxos)

    # create genesis transaction, which sends 100 coins to wallet_one
    genesis_transaction = get_genesis_transaction(wallet_coinbase, wallet_one, 100, utxos)

    print("Creating and mining genesis block")
    genesis = Block("0")
    genesis.add_transaction(genesis_transaction, utxos, minimum_transaction)

    blockchain.append_block(genesis)

    # testing
    print("Wallet one balance: %d" % wallet_one.get_balance())

    print()
    print("Attemping to send funds (40) to Wallet two")
    block1 = Block(genesis.hash)
    block1.add_transaction(wallet_one.send_funds(wallet_two.public_key_as_str(), 40), utxos, minimum_transaction)
    blockchain.append_block(block1)
    print("Wallet one balance: %d" % wallet_one.get_balance())
    print("Wallet two balance: %d" % wallet_two.get_balance())

    print()
    print("Block 1")
    block1.print()

    print()
    print("Attempting to send more funds (1000) than it has")
    block2 = Block(block1.hash)
    block2.add_transaction(wallet_one.send_funds(wallet_two.public_key_as_str(), 1000), utxos, minimum_transaction)
    blockchain.append_block(block2)
    print("Wallet one balance: %d" % wallet_one.get_balance())
    print("Wallet two balance: %d" % wallet_two.get_balance())

    print()
    print("Block 2")
    block2.print()

    print("Wallet two is attempting to send funds (20) to wallet one")
    block3 = Block(block2.hash)
    block3.add_transaction(wallet_two.send_funds(wallet_one.public_key_as_str(), 20), utxos, minimum_transaction)
    blockchain.append_block(block3)
    print("Wallet one balance: %d" % wallet_one.get_balance())
    print("Wallet two balance: %d" % wallet_two.get_balance())

    print()
    print("Block 3")
    block3.print()

    print("is chain valid?", blockchain.check_valid(genesis_transaction))
"""
