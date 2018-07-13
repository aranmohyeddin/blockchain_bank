# from blockchain import Block, BlockChain, Wallet, Transaction
# from blockchain import TransactionOutput
# from blockchain.genesis import get_genesis_transaction
from typing import Dict

import psycopg2

import json
import cmd, sys #cmd is used for making a repl.
from django.core.exceptions import ObjectDoesNotExist

# Django specific settings
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

# Ensure settings are read
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

# Your application specific imports
from banking.models import Customer, BankSettings, Bank, Manager, Wallet, Login
# from blockchain.models import BlockChain, Block, Transaction, TransactionInput, TransactionOutput, Sequence
from blockchain.block import Block
from blockchain.blockchain import BlockChain
from blockchain.transaction import Transaction
from blockchain.transaction_input import TransactionInput
from blockchain.transaction_output import TransactionOutput


class Shell_interface(cmd.Cmd):
    intro = 'Welcome to the international banks blockchain shell.\n\
            Type help or ? to list commands.\n'
    prompt = '(bch_bank)$ '
    file = None
    current_user = None
    flag = 0

    blockchain = None
    minimum_transaction = 5

    @staticmethod
    def _get_variable_with_type(prompt, type):
        while True:
            try:
                value = input(prompt)
                value = type(value)
                break
            except ValueError:
                print('Invalid Input')
        return value

    def _read_block_from_dict(self, dict):
        # print(dict)
        previous_hash = dict['prev_block']
        block = Block(previous_hash=previous_hash)
        block.hash = dict['hash']
        block.nonce = dict['nonce']
        block.timestamp = dict['time_stamp']
        for transaction_dict in dict['transactions']:
            sender = None
            if 'sender_public_key' in transaction_dict:
                sender = transaction_dict['sender_public_key']
            reciever = transaction_dict['receiver_public_key']
            value = transaction_dict['value']
            transaction_inputs = []
            if 'input' in transaction_dict:
                for transaction_input_dict in transaction_dict['input']:
                    transaction_output_id = transaction_input_dict['transactionOutputId']
                    transaction_input = TransactionInput(transaction_output_id=transaction_output_id)
                    transaction_inputs.append(transaction_input)
            transaction = Transaction(sender, reciever, value, transaction_inputs)
            block.add_transaction(transaction, all_utxos=self.blockchain.all_utxos,
                                  minimum_transaction=self.minimum_transaction,
                                  should_check=False)
            is_coinbase = False
            if 'output' in transaction_dict:
                for transaction_output_dict in transaction_dict['output']:
                    value = transaction_output_dict['value']
                    parent_transaction_id = ''
                    if 'parent_transaction_id' in transaction_output_dict:
                        parent_transaction_id = transaction_output_dict['parent_transaction_id']
                    recipient_public_key = transaction_output_dict['recipient_public_key']
                    transaction_output = TransactionOutput(recipient_public_key_str=recipient_public_key,
                                                           value=value,
                                                           parent_transaction_id=parent_transaction_id)
                    self.blockchain.append_utxo(transaction_output)
            self.blockchain.append_block(block)

    def _block_to_dict(self, block):
        block_dict = {
            'hash': block.hash,
            'previous_hash': block.previous_hash,
            'nonce': block.nonce,
            'time_stamp': block.timestamp,
            'transactions': []
        }
        transactions = Transaction.objects.filter(block=block)
        for transaction in transactions:
            transaction_dict = {
                'value': float(transaction.value),
                'id': transaction.id,
                'sender_public_key': transaction.sender,
                'receiver_public_key': transaction.recipient,
                'signature': transaction.signature,
                'input': [],
                'output': []
            }
            tis = TransactionInput.objects.filter(parent_transaction__id=transaction.id)
            for ti in tis:
                ti_dict = {
                    'transaction_output_id': ti.transaction_output_id,
                }
                transaction_dict['input'].append(ti_dict)
            tos = TransactionOutput.objects.filter(parent_transaction__id=transaction.id)
            for to in tos:
                to_dict = {
                    'id': to.id,
                    'value': float(to.value),
                    'recipient_public_key': to.recipient,
                    'spent': to.spent
                }
                transaction_dict['output'].append(to_dict)
            block_dict['transactions'].append(transaction_dict)
        return block_dict

    def do_create_manager(self, arg):
        '    Create the acount for the manager of all banking systems:\n\
                create Manager "ManagerUserName" "Password"'
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

    def do_get_json(self, arg):
        '''
        get "json_address"
        read genesis transaction from json file

        :param arg: string json_address
        :return:
        '''
        json_address = arg.strip('"')

        self.blockchain = BlockChain(BankSettings.objects.all()[0].difficulty)

        with open(json_address, 'r') as json_file:
            json_data = json.load(json_file)
            if type(json_data).__name__ == 'list':
                for item in json_data:
                    self._read_block_from_dict(item)
            else:  # it was a dict
                self._read_block_from_dict(json_data)

    def do_show_keys(self, arg):
        '    Show your Public Key and private Key:\n\
                show_keys'
        if not self.current_user:
            print('Show what keys!!!?\nYou have to login fist!')
        elif self.current_user.__class__.__name__ == 'Manager':
            print('Sorry dear Governor of the Central Bank, you can not have a wallet due to the regulations you have created yourself!')
        else:
            print("{}\n{}".format(*self.current_user.get_keys()))


    def do_register_bank(self, arg):
        '    Register a new bank:\n\
                register_bank "BankUserName" "Password" "Bank Name" "Token"'
        args = arg.split()
        if args[3] != BankSettings.objects.all()[0].generate_token:
            print("Wrong token, please contact the Governor of the Central Bank to get the right token")
        else:
            if Login.objects.filter(username=args[0]):
                print('User with username {} exists'.format(args[0]))
                return
            if Bank.objects.filter(name=args[2]).count() > 0:
                print('Bank with name {} exists'.format(args[2]))
                return
            bank = Bank()
            bank.init(*args[:3]).save()
            bank.create_wallet().save()
            bank.wallet.set_bank(bank)
            bank.wallet.save()
            print("{}\n{}".format(*bank.get_keys()))


    def do_register_customer(self, arg):
        '    Register a new Customer to a bank:\n\
                register_customer "CustomerUserName" "Password" "Bank Name"'
        args = arg.split()
        if Login.objects.filter(username=args[0]):
            print('User with username {} exists'.format(args[0]))
            return
        if not Bank.objects.filter(name=args[2]):
            print('The bank {} is not registered in the system.'.format(args[2]))
            return
        c = Customer().init(*args)
        c.save()
        print("Public key: {}\nPrivate key: {}".format(*c.get_keys()))


    def do_login(self, arg):
        '    Login:\n\
                login "UserName" "Password"'
        if self.current_user is None:
            uname, passwd = arg.split()
            try:
                user = Login.objects.get(username=uname)
                if user.authenticate(passwd):
                    print('you logged in as {}'.format(user.get_user_type_display()))
                    self.current_user = user.model.objects.get(login=user)
                else:
                    raise ValueError('password ncorrect')
            except (ObjectDoesNotExist, ValueError) as e:
                if self.flag == 0:
                    print("Authentication failed, If you don't know the password, please don't try again!")
                    self.flag = 1
                else:
                    print("System hacked successfully! Cops are on their way. Please run!")
                    self.flag = 0
        else:
            print("Please logout first!")


    def do_get_balance(self, arg):
        '    Get Balance:\n\
                get_balance'
        if not self.current_user:
            print('you must login first')
            return
        if self.current_user.login.user_type == 3:
            print('Manager has no wallet, and no wallet means no balance')
            return
        # the next two line should change to get logon person's wallet
        balance = self.current_user.get_balance()
        print("You currently have {}$ in your wallet".format(balance))


    def do_login_based_transfer(self, arg):
        '    Transfer some money to a wallet:\n\
                login_based_transfer x$ to "wallet_ID"'
        print("you don't have enough balance")


    def do_key_based_transfer(self, arg):
        '    Send transaction:\n\
                key_based_transfer x$ "PublicKey" "PrivateKey" to "publickey"'
        args = arg.split()
        w = Wallet.objects.get(pub = args[0])


    def do_request_loan(self, arg):
        '    Request for loan from bank:\n\
                request_loan x$'
        if not self.current_user:
            print('you must login first')
            return
        if self.current_user.login.user_type == 3:
            print('Manager has no wallet, and no wallet means no loan')
            return
        balance = self.current_user.wallet.get_balance()
        bank_balance = self.current_user.get_bank().get_balance()
        margin = BankSettings.objects.all()[0].loan_condition
        if balance < bank_balance + margin:
            # check if current_user has no failed transactions and send transaction
            pass


    def do_show_transactions_history(self, arg):
        '    Show transaction history(both incoming and outgoing):\n\
                show_transactions_history'
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

    def do_show_blockchain(self, arg):# access management
        '    Show BlockChain(manager only):\n\
                show_blockchain'
        blocks = Block.objects.filter(blockchain=self.blockchain)
        blocks_list = []
        for block in blocks:
            blocks_list.append(self._block_to_dict(block))
        print(json.dumps(blocks_list, sort_keys=True, indent=4))

    def do_show_blockchain_balance(self, arg):# access management
        '    Show BlockChain balance(manager only):\n\
                show_blockchain_balance'

    def do_show_invalid_transactions(self, arg):# access management
        '    Show Invalid transactons(manager can view all, each bank can view the ones within their own network):\n\
                show_invalid_transactions'

    def do_show_customers(self, arg):# access management
        '    Show Customers(manager can view all, each bank can view the ones within their own network):\n\
                show_customers'

    def do_logout(self, arg):
        '    Logout:\n\
                logout'
        self.current_user = None


    def do_quit(self, arg):
        '    Quit the Shell:\n\
                quit'
        print('Thank you for using the blockchain bank system')
        return True

    def do_clear(self, arg):
        '   Clear console:\n\
                clear'
        os.system('clear')


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
