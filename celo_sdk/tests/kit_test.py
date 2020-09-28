import time
import unittest

from web3 import Web3

from celo_sdk.kit import Kit
from celo_sdk.tests import test_data


class TestKit(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.kit = Kit('http://127.0.0.1:8545')
        self.governance_wrapper = self.kit.base_wrapper.create_and_get_contract_by_name(
            'Governance')
        self.kit.wallet_add_new_key = test_data.pk2
    
    def test_net_config(self):
        print(self.kit.get_network_config())