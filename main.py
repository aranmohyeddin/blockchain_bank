# from blockchain import Block, BlockChain, Wallet, Transaction
# from blockchain import TransactionOutput
# from blockchain.genesis import get_genesis_transaction
from typing import Dict

import psycopg2

import json
import cmd, sys #cmd is used for making a repl.

# Django specific settings
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

# Ensure settings are read
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

# Your application specific imports
from banking.models import Customer, BankSettings, Bank, Manager
from blockchain.models import BlockChain, Block, Transaction, TransactionInput, TransactionOutput, Sequence


class Shell_interface(cmd.Cmd):
    intro = 'Welcome to the international banks blockchain shell.\n\
            Type help or ? to list commands.\n'
    prompt = '(bch_bank)$ '
    file = None
    current_user = None;
    flag = 0;

    blockchain = None

    def _get_variable_with_type(self, prompt, type):
        while True:
            try:
                value = input(prompt)
                value = type(value)
                break
            except ValueError:
                print('Invalid Input')
        return value

    def _read_block_from_dict(self, dict):
        block = None
        transaction = None
        try:
            block = Block(
                hash=dict['hash'],
                previous_hash=dict['prev_block'],
                nonce=dict['nonce'],
                timestamp=dict['time_stamp']
            )
            block.blockchain = self.blockchain
            block.save()
            for transaction_dict in dict['transactions']:
                transaction = Transaction(
                    value=transaction_dict['value'],
                    id=transaction_dict['id'],
                    sender=transaction_dict['sender_public_key'],
                    recipient=transaction_dict['receiver_public_key'],
                    signature=transaction_dict['signature']
                )
                transaction.block = block
                transaction.save()
                for input_dict in transaction_dict['input']:
                    # ti = TransactionInput()
                    pass
                for output_dict in transaction_dict['output']:
                    to = TransactionOutput(
                        id=output_dict['id'],
                        value=output_dict['value'],
                        recipient=output_dict['recipient_public_key'],
                        spent=output_dict['spent']
                    )
                    if transaction.id != output_dict['parent_transaction_id']:
                        print('Something seems wrong parent_id does not match')
                    to.parent_transaction = transaction
                    to.save()
        except KeyError as err:
            print('KeyError: {}'.format(err))
            if block:
                block.delete()
            if transaction:
                transaction.delete()

    def do_1(self, arg):
        '    Create the acount for the manager of all banking systems:\n\
                Create Manager "ManagerUserName" "Password"'
        args = arg.split()
        manager_username = args[0]
        manager_password = args[1]

        manager_username = manager_username.strip('"')
        manager_password = manager_password.strip('"')

        manager = Manager()
        manager.init(manager_username, manager_password)
        manager.save()

        transaction_count_on_block = self._get_variable_with_type('Number of Transaction In Block: ', int)
        fee = self._get_variable_with_type('Transaction Fee: ', float)
        reward = self._get_variable_with_type('Block Mining Reward:', float)
        difficulty = self._get_variable_with_type('Difficulty: ', int)
        generate_token = self._get_variable_with_type('Generate Token: ', str)
        loan_condition = self._get_variable_with_type('Remainig bank balance more than this after Loan: ', float)
        bank_settings = BankSettings(
            transaction_count_on_block=transaction_count_on_block,
            fee=fee,
            reward=reward,
            difficulty=difficulty,
            generate_token=generate_token,
            loan_condition=loan_condition
        )
        bank_settings.save()

    def do_2(self, arg):
        '''
        Get "json_address"
        read genesis transaction from json file

        :param arg: string json_address
        :return:
        '''
        json_address = arg.strip('"')

        difficulty = BankSettings.objects.all()[0].difficulty
        self.blockchain = BlockChain(difficulty=difficulty)
        self.blockchain.save()

        with open(json_address, 'r') as json_file:
            json_data = json.load(json_file)
            if type(json_data) == 'list':
                for item in json_data:
                    self._read_block_from_dict(item)
            else:  # it was a dict
                self._read_block_from_dict(json_data)
        seq = Sequence(value=Transaction.objects.count())
        seq.save()

    def do_3(self, arg):
        '    Show your Public Key and private Key:\n\
                3'
        print("Public key: {}\nPrivate key: {}".format(*self.current_user.get_keys))


    def do_4(self, arg):
        '    Register a new bank:\n\
                4 "BankUserName" "Password" "Bank Name" "Token"'
        args = arg.split()
        if args[3] != BankSettings.objects.all()[0].generate_token:
            print("Wrong token, please contact the Governor of the Central Bank to get the right token")
        else:
            b = Bank()
            b.init(*args[1:3])
            b.create_wallet()
            print(b.get_keys()[0])
            b.save()


    def do_5(self, arg):
        '    Register a new Customer to a bank:\n\
                5 "CustomerUserName" "Password" "Bank Name"'
        c = Customer().init(*arg.split())
        print(c.get_keys()[0])
        c.save()


    def do_6(self, arg):
        '    Login:\n\
                6 "UserName" "Password"'
        uname, passwd = arg.split()
        user = Customer.objects.get(username=uname)[0]
        if user.authenticate(passwd):
            current_user = user
            print("Welcome dear {} from bank {}".format(uname, user.wallet.bank))
        else:
            if self.flag == 0:
                print("Authentication failed, If you don't know the password, please don't try again!")
                self.flag = 1
            else:
                print("System hacked successfully! Cops are on their way. Please run!")


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
        current_user = None


    def do_quit(self, arg):
        '    Quit the Shell:\n\
                quit'
        logout()
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
