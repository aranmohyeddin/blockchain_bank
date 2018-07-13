import threading
import time
from blockchain import Transaction, Block
from banking.models import BankSettings

_delay = .1

class Miner(threading.Thread):


    def __init__(self, shell, bank):
        threading.Thread.__init__(self)
        self.shell = shell
        self.bank = bank


    def _try_to_mine(self):
        fee = float(BankSettings.objects.all()[0].fee)
        valid_transactions = []
        for tid, not_mined_transaction in self.shell.blockchain.not_mined_transactions.items():
            if (len(valid_transactions) < self.shell.block_size - 1 and
                    not_mined_transaction.is_valid(self.shell.blockchain.all_utxos,
                                                   self.shell.blockchain.minimum_transaction, fee)):
                valid_transactions.append(not_mined_transaction)
        if len(valid_transactions) < self.shell.block_size - 1:
            return
        block = Block(self.shell.blockchain.last_block_hash())

        value = float(BankSettings.objects.all()[0].reward) + fee * (self.shell.block_size - 1)
        coinbase = Transaction('', self.bank.wallet.get_keys()[0], value=value, inputs=[])
        block.add_transaction(transaction=coinbase,
                              all_utxos=self.shell.blockchain.all_utxos,
                              minimum_transaction=self.shell.blockchain.minimum_transaction,
                              fee=fee, should_check=True, is_coinbase=True)
        self.shell.blockchain.append_transaction(coinbase)
        for valid_transaction in valid_transactions:
            block.add_transaction(valid_transaction, self.shell.blockchain.all_utxos,
                                  self.shell.blockchain.minimum_transaction,
                                  fee=fee, should_check=True)
        block.mine(BankSettings.objects.all()[0].difficulty)
        print('block mined: {}'.format(block.calculate_hash()))
        self.shell.blockchain.append_block(block)

    def run(self):
        print("Bank {} started mining.".format(self.bank.name))
        while not self.shell.exit_threads:
            self.shell.lock.acquire()
            try:
                if len(self.shell.blockchain.not_mined_transactions) >= self.shell.block_size - 1:
                    self._try_to_mine()
            finally:
                self.shell.lock.release()
            time.sleep(_delay)
        print("Bank {} stopped mining.".format(self.bank.name))


