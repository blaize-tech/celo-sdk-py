import time
import unittest

from web3 import Web3

from sdk.kit import Kit
from sdk.tests import test_data


class TestReserveWrapper(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.kit = Kit('https://alfajores-forno.celo-testnet.org')
        self.reserve_wrapper = self.kit.base_wrapper.create_and_get_contract_by_name(
            'Reserve')
        self.kit.wallet_add_new_key = test_data.pk1
    
    def test_get_spenders(self):
        print(self.reserve_wrapper.get_spenders())