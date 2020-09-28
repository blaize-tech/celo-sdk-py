import time
import unittest

from web3 import Web3

from celo_sdk.kit import Kit
from celo_sdk.tests import test_data


class TestKit(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.kit = Kit('http://localhost:8544')
        self.governance_wrapper = self.kit.base_wrapper.create_and_get_contract_by_name(
            'Governance')
        self.kit.wallet.sign_with_provider = True
        for _, v in test_data.deriv_pks.items():
            self.kit.wallet_add_new_key = v
        
        self.accounts = self.kit.w3.eth.accounts

        self.kit.w3.eth.defaultAccount = self.accounts[0]
        self.kit.wallet_change_account = self.accounts[0]
    
    def test_net_config(self):
        print(self.kit.get_network_config())