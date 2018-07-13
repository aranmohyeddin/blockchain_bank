from blockchain import Block, Transaction
from blockchain import TransactionInput

class BlockChain:

    def __init__(self, difficulty):
        self.blocks = []
        self.difficulty = difficulty
        self.all_utxos = {}
        self.all_transactions = {}

    def append_block(self, block: Block):  #, mine_block=True):
        # if mine_block:
        #     block.mine(self.difficulty)
        #     print("Block mined: " + block.hash)

        # todo -> should lock here after threading
        if block.previous_hash != "0" and block.previous_hash != self.blocks[-1].hash:
            print('Invalid block. previous_hash does not match')
            return

        for transaction in block.transactions:
            if transaction.transaction_id in self.all_transactions:
                self.all_transactions[transaction.transaction_id].mined = True
            else:
                print('It seems something is wrong, we didnt have this transacation')

            for transaction_input in transaction.inputs:
                del self.all_utxos[transaction_input.transaction_output_id]

            for transaction_output in transaction.outputs:
                self.all_utxos[transaction_output.id] = transaction_output
        self.blocks.append(block)

    def append_transaction(self, transaction):
        self.all_transactions[transaction.transaction_id] = transaction

    def append_utxo(self, transaction_output):
        self.all_utxos[transaction_output.id] = transaction_output

    def check_valid(self, genesis_transaction: Transaction):
        hash_prefix = "0" * self.difficulty

        temp_utxos = dict()  # a temperory dictionary of unspent transactions
        temp_utxos[genesis_transaction.outputs[0].id] = genesis_transaction.outputs[0]

        prev_hash = self.blocks[0].hash
        for block_ind in range(1, len(self.blocks)):
            print("Checking block %d" % block_ind)

            block = self.blocks[block_ind]

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
            for transaction in block.transactions:
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
        if self.blocks:
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

    def get_balance_for_public_key(self, public_key):
        amount = 0

        for transaction_output_id, utxo in self.all_utxos.items():
            if utxo.is_mine(public_key):
                amount += utxo.value

        return amount

    def send_funds_from_to(self, sender_public_key_str: str, sender_private_key_str: str,
                           recipient_public_key_str: str, value: float):
        if self.get_balance_for_public_key(sender_public_key_str) < value:
            print("Not enough balance, transaction discarded")
            return

        if value <= 0:
            print("Value should be positive, transaction discarded")
            return

        inputs = []
        total = 0
        for transaction_id, utxo in self.all_utxos.items():
            if utxo.is_mine(sender_public_key_str):
                total += utxo.value
                inp = TransactionInput(transaction_id)
                inputs.append(inp)

                if total >= value:
                    break

        transaction = Transaction(sender_public_key_str, recipient_public_key_str, value, inputs)
        transaction.generate_signature(sender_private_key_str)

        return transaction