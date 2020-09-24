import time
import unittest

from web3 import Web3

from sdk.kit import Kit
from sdk.tests import test_data


class TestLockedGoldWrapper(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.kit = Kit('https://alfajores-forno.celo-testnet.org')
        self.locked_gold_wrapper = self.kit.base_wrapper.create_and_get_contract_by_name(
            'LockedGold')
        self.kit.wallet_add_new_key = test_data.pk1
        self.kit.wallet_add_new_key = test_data.pk2

        self.value = 120938732980
    
    def test_alock_gold(self):
        self.assertTrue(self.locked_gold_wrapper.lock({'value': self.value}))
        time.sleep(1)
    
    def test_bunlock_gold(self):
        self.assertTrue(self.locked_gold_wrapper.unlock(self.value))
        time.sleep(1)
    
    def test_crelock_gold(self):
        accounts = list(self.kit.wallet.accounts.values())[1:]

        self.assertTrue(self.locked_gold_wrapper.lock({'value': self.value}))
        time.sleep(2)
        self.assertTrue(self.locked_gold_wrapper.unlock(self.value))
        time.sleep(2)
        self.assertTrue(self.locked_gold_wrapper.unlock(self.value))
        time.sleep(2)
        self.assertTrue(self.locked_gold_wrapper.unlock(self.value))
        time.sleep(2)

        self.assertTrue(self.locked_gold_wrapper.relock(accounts[1].address, self.value * 2.5))