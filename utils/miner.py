import threading
import time


_delay = .1

class Miner(threading.Thread):


    def __init__(self, shell, bank_name):
        threading.Thread.__init__(self)
        self.shell = shell
        self.bank_name = bank_name


    def run(self):
        print("Bank {} started mining.".format(self.bank_name))
        while not self.shell.exit_threads:
            self.shell.lock.acquire()
            try:
                if len(self.shell.blockchain.not_mined_transactions) >= self.shell.block_size - 1:
                    self.shell.blockchain.append_new_block()
            finally:
                self.shell.lock.release()
            time.sleep(_delay)
        print("Bank {} stopped mining.".format(self.bank_name))


