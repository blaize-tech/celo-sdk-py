import time
import unittest

from web3 import Web3

from sdk.kit import Kit
from sdk.tests import test_data


class TestAttestationsWrapper(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.kit = Kit('https://alfajores-forno.celo-testnet.org')
        self.attestations_wrapper = self.kit.base_wrapper.create_and_get_contract_by_name(
            'Attestations')
        self.kit.wallet_add_new_key = test_data.pk2
    
    def test_attestation_expiry_blocks(self):
        call = self.attestations_wrapper.attestation_expiry_blocks()
        self.assertEqual(type(call), int)