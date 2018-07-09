from crypto.utils import generate_rsa_keys

class Wallet():
    wallet_id = None
    bank = None
    pub = None
    pv = None


    def __init__(self, wallet_id, bank):
        self.wallet_id = wallet_id
        self.bank = bank
        self.pv, self.pub = generate_rsa_keys():

