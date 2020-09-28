import time
import unittest

from web3 import Web3

from celo_sdk.kit import Kit
from celo_sdk.tests import test_data


class TestLockedGoldWrapper(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.kit = Kit('https://alfajores-forno.celo-testnet.org')
        self.locked_gold_wrapper = self.kit.base_wrapper.create_and_get_contract_by_name(
            'LockedGold')
        self.accounts_wrapper = self.kit.base_wrapper.create_and_get_contract_by_name(
            'Accounts')
        self.kit.wallet.sign_with_provider = True
        for _, v in test_data.deriv_pks.items():
            self.kit.wallet_add_new_key = v
        
        self.accounts = self.kit.w3.eth.accounts

        self.kit.w3.eth.defaultAccount = self.accounts[0]
        self.kit.wallet_change_account = self.accounts[0]

        self.value = 120938732980

    def test_lock_gold(self):
        self.assertTrue(self.locked_gold_wrapper.lock({'value': self.value}))

    def test_unlock_gold(self):
        self.assertTrue(self.locked_gold_wrapper.unlock(self.value))

    def test_relock_gold(self):

        self.assertTrue(self.locked_gold_wrapper.lock({'value': self.value}))
        self.assertTrue(self.locked_gold_wrapper.unlock(self.value))
        self.assertTrue(self.locked_gold_wrapper.unlock(self.value))
        self.assertTrue(self.locked_gold_wrapper.unlock(self.value))

        self.assertTrue(self.locked_gold_wrapper.relock(
            self.accounts[1], self.value * 2.5))
