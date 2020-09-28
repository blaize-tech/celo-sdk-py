import time
import unittest
from unittest.mock import Mock

from web3 import Web3

from celo_sdk.kit import Kit
from celo_sdk.tests import test_data


class TestExchangeWrapper(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.kit = Kit('http://localhost:8544')
        self.exchange_wrapper = self.kit.base_wrapper.create_and_get_contract_by_name(
            'Exchange')
        self.kit.wallet.sign_with_provider = True
        for _, v in test_data.deriv_pks.items():
            self.kit.wallet_add_new_key = v
        
        self.accounts = self.kit.w3.eth.accounts

        self.one = self.kit.w3.toWei(1, 'ether')
        self.large_buy_amount = self.kit.w3.toWei(1000, 'ether')

    def test_check_buckets(self):
        buy_bucket, sell_bucket = self.exchange_wrapper.get_buy_and_sell_buckets(True)

        self.assertEqual(type(buy_bucket), int)
        self.assertEqual(type(sell_bucket), int)

        self.assertTrue(buy_bucket > 0)
        self.assertTrue(sell_bucket > 0)

    def test_quote_usd_sell(self):
        self.assertEqual(type(self.exchange_wrapper.quote_usd_sell(self.one)), int)

    def test_quote_gold_sell(self):
        self.assertEqual(type(self.exchange_wrapper.quote_gold_sell(self.one)), int)

    def test_quote_usd_buy(self):
        self.assertEqual(type(self.exchange_wrapper.quote_usd_buy(self.one)), int)

    def test_quote_gold_buy(self):
        self.assertEqual(type(self.exchange_wrapper.quote_gold_buy(self.one)), int)

    def test_sell_dollar(self):
        gold_amount = self.exchange_wrapper.quote_usd_sell(self.one)
        stable_token_wrapper = self.kit.base_wrapper.create_and_get_contract_by_name('StableToken')
        approve_tx = stable_token_wrapper.approve(self.exchange_wrapper.address, self.one)
        time.sleep(3)
        sell_tx = self.exchange_wrapper.sell_dollar(self.one, gold_amount)
        
        self.assertEqual(type(sell_tx), bytes)
    
    def test_sell_gold(self):
        usd_amount = self.exchange_wrapper.quote_gold_sell(self.one)
        gold_token_wrapper = self.kit.base_wrapper.create_and_get_contract_by_name('GoldToken')
        approve_tx = gold_token_wrapper.approve(self.exchange_wrapper.address, self.one)
        time.sleep(8)
        sell_tx = self.exchange_wrapper.sell_gold(self.one, usd_amount)

        self.assertTrue(sell_tx)

    def test_get_gold_exchange_rate(self):
        self.assertTrue(self.exchange_wrapper.get_exchange_rate(self.large_buy_amount, True) > 0)

    def test_get_dollar_exchange_rate(self):
        self.assertTrue(self.exchange_wrapper.get_usd_exchange_rate(self.large_buy_amount) > 0)