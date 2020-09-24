import time
import unittest

from web3 import Web3

from sdk.kit import Kit
from sdk.tests import test_data


class TestReleaseGoldWrapper(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.kit = Kit('https://alfajores-forno.celo-testnet.org')
        self.release_gold_wrapper = self.kit.base_wrapper.create_and_get_contract_by_name(
            'ReleaseGold')
        self.kit.wallet_add_new_key = test_data.pk1
    
    def test_get_release_schedule(self):
        print(self.release_gold_wrapper._contract.functions.releaseSchedule())