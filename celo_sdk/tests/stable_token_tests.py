import time
import unittest

from web3 import Web3

from celo_sdk.kit import Kit
from celo_sdk.tests import test_data


class TestStableTokenWrapper(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.kit = Kit('http://localhost:8544')
        self.stable_token_wrapper = self.kit.base_wrapper.create_and_get_contract_by_name(
            'StableToken')
        self.kit.wallet.sign_with_provider = True
        self.accounts = self.kit.w3.eth.accounts

        for _, v in test_data.deriv_pks.items():
            self.kit.wallet_add_new_key = v
        
        self.kit.w3.eth.defaultAccount = self.accounts[0]
        self.kit.wallet_change_account = self.accounts[0]

    def test_name(self):
        name = self.stable_token_wrapper.name()
        self.assertEqual(name, 'Celo Dollar')

    def test_symbol(self):
        symbol = self.stable_token_wrapper.symbol()
        self.assertEqual(symbol, 'cUSD')

    def test_decimals(self):
        decimals = self.stable_token_wrapper.decimals()
        self.assertEqual(decimals, 18)

    def test_total_supply(self):
        total_supply = self.stable_token_wrapper.total_supply()
        self.assertEqual(type(total_supply), int)

    def test_balance_of(self):
        balance = self.stable_token_wrapper.balance_of(self.accounts[0])
        self.assertEqual(type(balance), int)

    def test_owner(self):
        owner = self.stable_token_wrapper.owner()
        self.assertEqual(self.kit.w3.isAddress(owner), True)

    def test_get_inflation_parameters(self):
        infl_params = self.stable_token_wrapper.get_inflation_parameters()
        self.assertEqual(type(infl_params), dict)

    def test_transfer(self):
        initial_balance_2 = self.stable_token_wrapper.balance_of(
            self.accounts[1])

        tx_hash = self.stable_token_wrapper.transfer(
            self.accounts[1], self.kit.w3.toWei(1, 'ether'))

        self.assertEqual(type(tx_hash), str)

        time.sleep(5)  # wait until transaction finalized

        final_balance_2 = self.stable_token_wrapper.balance_of(
            self.accounts[1])

        self.assertEqual(final_balance_2, initial_balance_2 +
                         self.kit.w3.toWei(1, 'ether'))

    def test_transfer_from(self):
        tx_hash = self.stable_token_wrapper.increase_allowance(self.accounts[1], self.kit.w3.toWei(1, 'ether'))

        self.assertEqual(type(tx_hash), str)

        self.kit.w3.eth.defaultAccount = self.accounts[1]
        self.kit.wallet_change_account = self.accounts[1]
        initial_balance_3 = self.stable_token_wrapper.balance_of(
            test_data.address3)
        tx_hash = self.stable_token_wrapper.transfer_from(self.accounts[0], self.accounts[2], self.kit.w3.toWei(1, 'ether'))

        time.sleep(5)

        final_balance_3 = self.stable_token_wrapper.balance_of(
            self.accounts[2])
        
        self.assertEqual(final_balance_3, initial_balance_3 + self.kit.w3.toWei(1, 'ether'))
