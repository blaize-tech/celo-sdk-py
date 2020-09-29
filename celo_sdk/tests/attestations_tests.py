import time
import unittest
from unittest.mock import Mock

from web3 import Web3

from celo_sdk.kit import Kit
from celo_sdk.tests import test_data
from celo_sdk.utils import phone_number_utils


class TestAttestationsWrapper(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.kit = Kit('http://localhost:8544')
        self.attestations_wrapper = self.kit.base_wrapper.create_and_get_contract_by_name(
            'Attestations')
        self.kit.wallet.sign_with_provider = True
        for _, v in test_data.deriv_pks.items():
            self.kit.wallet_add_new_key = v
        
        self.accounts = self.kit.w3.eth.accounts

        self.phone_number = '+15555555555'
        self.identifier = phone_number_utils.get_phone_hash(self.kit.w3.soliditySha3, self.phone_number)
    
    def test_no_completions(self):
        mock = Mock()
        mock.return_value = {'completed': 0, 'total': 3}
        self.attestations_wrapper.get_attestation_stat = mock

        result = self.attestations_wrapper.get_verified_status(self.identifier, self.accounts[0])

        self.assertFalse(result['is_verified'])
        self.assertEqual(result['num_attestations_remaining'], 3)
    
    def test_not_enough_completions(self):
        mock = Mock()
        mock.return_value = {'completed': 2, 'total': 6}
        self.attestations_wrapper.get_attestation_stat = mock

        result = self.attestations_wrapper.get_verified_status(self.identifier, self.accounts[0])

        self.assertFalse(result['is_verified'])
        self.assertEqual(result['num_attestations_remaining'], 1)
    
    def test_fraction_too_low(self):
        mock = Mock()
        mock.return_value = {'completed': 3, 'total': 30}
        self.attestations_wrapper.get_attestation_stat = mock

        result = self.attestations_wrapper.get_verified_status(self.identifier, self.accounts[0])

        self.assertFalse(result['is_verified'])
    
    def test_fraction_pass_threshold(self):
        mock = Mock()
        mock.return_value = {'completed': 3, 'total': 9}
        self.attestations_wrapper.get_attestation_stat = mock

        result = self.attestations_wrapper.get_verified_status(self.identifier, self.accounts[0])

        self.assertTrue(result['is_verified'])