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
from banking.models import Customer, BankSettings, Bank, Manager, Wallet
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

    def do_show_keys(self, arg):
        '    Show your Public Key and private Key:\n\
                show_keys'
        print("Public key: {}\nPrivate key: {}".format(*self.current_user.get_keys))


    def do_register_bank(self, arg):
        '    Register a new bank:\n\
                register_bank "BankUserName" "Password" "Bank Name" "Token"'
        args = arg.split()
        if args[3] != BankSettings.objects.all()[0].generate_token:
            print("Wrong token, please contact the Governor of the Central Bank to get the right token")
        else:
            b = Bank().init(*args[1:3])
            b.create_wallet()
            print(b.get_keys()[0])
            b.save()


    def do_register_Customer(self, arg):
        '    Register a new Customer to a bank:\n\
                register_customer "CustomerUserName" "Password" "Bank Name"'
        args = arg.split()
        c = Customer().init(*args[:2]).create_wallet(args[2])
        print(c.get_keys()[0])
        c.save()


    def do_login(self, arg):
        '    Login:\n\
                login "UserName" "Password"'
        uname, passwd = arg.split()
        user = Login.objects.get(username=uname)[0].get_subclass()
        if user.authenticate(passwd):
            current_user = user
            clazz = user.__class__.__name__
            if clazz == 'Customer':
                print("Welcome dear {} from bank {}".format(uname, user.wallet.bank))
            elif clazz == 'Bank':
                print("Welcome dear manager of bank " + user.name)
            elif clazz == 'Manager':
                print("Welcome dear governor of the central bank! How shall we serve you?")
        else:
            if self.flag == 0:
                print("Authentication failed, If you don't know the password, please don't try again!")
                self.flag = 1
            else:
                print("System hacked successfully! Cops are on their way. Please run!")
                self.flag = 0


    def do_get_balance(self, arg):
        '    Get Balance:\n\
                get_balance'
        # the next two line should change to get logon person's wallet
        public_key = 'MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCyrHvUNwWQ9yEBJ5Cn1la4paiGpt6yip995PTUgN0zn7ELMXZF85prIk7FD3nPWAKNz1lKzPHTAxB1nKQWZ6/I0kQxwHcMdFE/XxPxHHgnsueQXX1Rj2sCKluj7jgTr6RlvCv6m8MdP7nd4MuLtB+WcI7OstFwcqVLBM6qUIzIFwIDAQAB'
        wallet = Wallet(pub=public_key)

        ballance = wallet.get_balance()
        print(ballance)


    def do_login_based_transfer(self, arg):
        '    Transfer some money to a wallet:\n\
                login_based_transfer x$ to "wallet_ID"'
        print("are you sure you want to transfer x to?")
        print("you don't have enough balance")


    def do_key_based_transfer(self, arg):
        '    Send transaction:\n\
                key_based_transfer x$ "PublicKey" "PrivateKey" to "publickey"'
        args = arg.split()
        w = Wallet.objects.get(pub = args[0])


    def do_request_loan(self, arg):
        '    Request for loan from bank:\n\
                request_loan x$ from "Bank Name"'


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

    def do_show_blockchain_balence(self, arg):# access management
        '    Show BlockChain balance(manager only):\n\
                show_blockchain_balence'

    def do_show_invalid_transactions(self, arg):# access management
        '    Show Invalid transactons(manager can view all, each bank can view the ones within their own network):\n\
                show_invalid_transactions'

    def do_show_customers(self, arg):# access management
        '    Show Customers(manager can view all, each bank can view the ones within their own network):\n\
                show_customers'

    def do_logout(self, arg):
        '    Logout:\n\
                logout'
        current_user = None


    def do_quit(self, arg):
        '    Quit the Shell:\n\
                quit'
        logout()
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
