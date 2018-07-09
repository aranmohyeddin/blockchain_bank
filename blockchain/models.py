from datetime import datetime
from crypto.utils import merkle_root
from django.db import models
from crypto.utils import sha256
from crypto.rsa import sign, verify, import_key
from typing import List, Dict
# from blockchain import TransactionOutput, TransactionInput

# from blockchain import Block, Transaction

from utils.models import SingletonModel


class BlockChain(SingletonModel):
    difficulty = models.IntegerField()

    def append_block(self, block, mine_block=True):
        if mine_block:
            block.mine(self.difficulty)
            print("Block mined: " + block.hash)

        self.block_set.add(block)

    def check_valid(self, genesis_transaction):
        hash_prefix = "0" * self.difficulty

        temp_utxos = dict()  # a temperory dictionary of unspent transactions
        temp_utxos[genesis_transaction.output_set.all()[0].id] = genesis_transaction.output_set.all()[0]

        prev_hash = self.block_set.all().order_by('timestamp')[0].hash
        for block_ind in range(1, self.block_set.count()):
            print("Checking block %d" % block_ind)

            block = self.block_set.all().order_by('timestamp')[block_ind]

            # compare registered hash and calculated hash
            if block.calculate_hash() != block.hash:
                print("Invalid hash")
                return False

            # check registered previous hash with its real previous hash
            if block.previous_hash != prev_hash:
                print("Invalid previous hash")
                return False

            prev_hash = block.hash

            # check if hash is solved
            if not block.hash.startswith(hash_prefix):
                print("Hash is not solved")
                return False

            # loop through transactions
            i = 0
            for transaction in block.transaction_set.all():
                if not transaction.verify_signature():
                    print("Signature is invalid on transaction %d" % i)
                    return False

                if transaction.get_inputs_value() != transaction.get_outputs_value():
                    print("Input values are not equal with output values on transaction %d" % i)
                    return False

                for inp in transaction.inputs:
                    output = temp_utxos.get(inp.transaction_output_id)

                    if not output:
                        print("Missing transaction input reference on transaction %d" % i)
                        return False

                    if output.value != inp.utxo.value:
                        print("Invalid transaction input value for transaction %d" % i)
                        return False

                    del temp_utxos[output.id]

                for output in transaction.outputs:
                    temp_utxos[output.id] = output

                if transaction.outputs[0].recipient != transaction.recipient:
                    print("Transaction output recipient is not who it should be on transaction %d" % i)
                    return False

                if transaction.get_inputs_value() != transaction.outputs[0].value \
                    and transaction.outputs[1].recipient != transaction.sender:

                    print("Transaction ouput `change` is not sender on transaction %d" % i)
                    return False

                i += 1

        return True

    def last_block_hash(self):
        if self.block_set.count() != 0:
            return self.blocks[-1].hash
        else:
            return "0"

    def append_new_block(self, mine=True):

        block = Block(self.last_block_hash())

        if mine:
            block.mine(self.difficulty)
            print("Block mined: " + block.hash)

        self.append_block(block)

        return block

    def print(self):
        index = 0

        for block in self.blocks:
            print("Block %d" % index)
            block.print()

            index += 1


class Block(models.Model):
    previous_hash = models.CharField(max_length=1024)
    nonce = models.IntegerField(default=0)
    hash = models.CharField(max_length=1024)
    timestamp = models.CharField(max_length=256)
    blockchain = models.ForeignKey(BlockChain, on_delete=models.CASCADE)

    def get_message(self):
        return self.previous_hash + str(self.nonce) + str(self.timestamp) + self.get_merkle_root()

    def calculate_hash(self):
        message = self.get_message()
        return sha256(message)

    def mine(self, difficulty=5):
        hash_prefix = '0' * difficulty

        while not self.hash.startswith(hash_prefix):
            self.nonce += 1
            self.hash = self.calculate_hash()

    def get_merkle_root(self) -> str:
        transaction_ids = [transaction.id for transaction in self.transaction_set]
        return merkle_root(transaction_ids)

    def add_transaction(self, transaction, all_utxos, minimum_transaction) -> bool:
        if transaction is None:
            return False

        # process transaction and check if valid, unless block is genesis block then ignore.
        if self.previous_hash != "0":
            if not transaction.process_transaction(all_utxos, minimum_transaction):
                print("Transaction failed to process")
                return False

        self.transaction_set.create(transaction)
        return True

    def save(self):
        if Block.objects.filter(hash=self.hash).count() > 0:
            Block.objects.filter(hash=self.hash).delete()
        super(Block, self).save()

    def __str__(self):
        return self.hash

    def print(self):
        print("hash:", self.hash)
        print("transactions_count", self.transaction_set.count())
        print("merkle_root:", self.get_merkle_root())
        print("timestamp:", self.timestamp)
        print("nounce:", self.nonce)
        print("prev_hash:", self.previous_hash)
        print()


class Sequence(SingletonModel):
    value = models.IntegerField()


class Transaction(models.Model):

    block = models.ForeignKey(Block, on_delete=models.CASCADE)
    sender = models.CharField(max_length=1024)
    recipient = models.CharField(max_length=1024)
    value = models.DecimalField(max_digits=24, decimal_places=4)

    signature = models.CharField(max_length=1024)
    id = models.CharField(max_length=1024, primary_key=True)

    def calculate_hash(self):
        # increase the sequence to avoid 2 identical transactions having the same hash
        seq = Sequence.objects.all()[0]
        seq.value += 1
        seq.save()

        message = self.sender + self.recipient + str(self.value) + str(seq.value)

        return sha256(message)

    def generate_signature(self, sender_private_key):
        message = self.sender + self.recipient + str(self.value)
        self.signature = sign(message.encode(), sender_private_key)

    def verify_signature(self):
        if not self.signature:
            return False

        message = self.sender + self.recipient + str(self.value)
        sender_public_key = import_key(self.sender)
        return verify(message.encode(), self.signature, sender_public_key)

    def get_outputs_value(self):

        amount = 0

        for output in self.output_set.all():
            amount += output.value

        return amount

    def get_inputs_value(self):

        amount = 0

        for input in self.input_set.all():
            if input.utxo:
                amount += input.utxo.value

        return amount

    # Returns true if new transaction could be created.
    def process_transaction(self, minimum_transaction: float):

        if not self.verify_signature():
            print("Transaction signature failed to verify")
            return False

        # gather transaction inputs (make sure they are unspent)
        for inp in self.input_set.all():
            try:
                inp.utxo = TransactionOutput.objects.get(id=inp.transaction_output_id, spent=False)
            except TransactionOutput.DoesNotExist:
                inp.utxo = None

        inputs_value = self.get_inputs_value()

        if inputs_value < minimum_transaction:
            print("Transaction inputs too small: " + str(inputs_value))
            return False

        if inputs_value < self.value:
            print("Transaction inputs are not sufficient to do transaction")

        self.id = self.calculate_hash()

        to = TransactionOutput(
            recipient_public_key_str=self.recipient,
            value=self.value,
            parent_transaction_id=self.id,
            spent=False
        )
        to.save()
        self.output_set.add(to)

        leftover_value = inputs_value - self.value
        if leftover_value > 0:
            to = TransactionOutput(
                recipient_public_key_str=self.sender,
                value=leftover_value,
                parent_transaction_id=self.id,
                spent=False
            )
            to.save()
            self.output_set.add(to)

        # add outputs to unspent utxos list
        # for output in self.output_set:
        #     all_utxos[output.id] = output

        # remove inputs from utxos list as spent
        for inp in self.input_set.all():
            if inp.utxo:
                inp.utxo.spent = True

        return True


class TransactionOutput(models.Model):
    """
    The result of doing a transaction
    """
    recipient = models.CharField(max_length=1024)
    value = models.DecimalField(max_digits=24, decimal_places=4)
    parent_transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='output')
    id = models.CharField(max_length=1024, primary_key=True)
    spent = models.BooleanField()

    def calculate_hash(self):
        message = self.recipient + str(self.value) + self.parent_transaction.id
        return sha256(message)

    def is_mine(self, public_key_str):
        return self.recipient == public_key_str


class TransactionInput(models.Model):
    transaction_output_id = models.CharField(max_length=1024)
    utxo = models.OneToOneField(TransactionOutput, on_delete=models.CASCADE, related_name='utxo')
    parent_transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='input')

#    def __init__(self, transaction_output_id: str):
#     def __init__(self, *args, **kwargs):
#         super(TransactionInput, self).__init__(*args, **kwargs)
        # self.utxo = None  # type: TransactionOutput
