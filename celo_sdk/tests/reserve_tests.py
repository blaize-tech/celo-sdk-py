import time
import unittest

from web3 import Web3

from celo_sdk.kit import Kit
from celo_sdk.tests import test_data


class TestReserveWrapper(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.kit = Kit('http://localhost:8544')
        self.reserve_wrapper = self.kit.base_wrapper.create_and_get_contract_by_name(
            'Reserve')        
        self.kit.wallet.sign_with_provider = True
        for _, v in test_data.deriv_pks.items():
            self.kit.wallet_add_new_key = v

        accounts = self.kit.w3.eth.accounts

        self.kit.w3.eth.defaultAccount = accounts[0]
        self.kit.wallet_change_account = accounts[0]

        self.other_reserve_address = accounts[9]
        self.other_spender = accounts[7]

        self.spenders = self.reserve_wrapper.get_spenders()
        # assumes that the multisig is the most recent spender in the spenders array
        self.multisig_address = self.spenders[-1] if len(self.spenders) > 0 else ''
        self.reserve_spender_multisig_wrapper = self.kit.base_wrapper.create_and_get_contract_by_name('MultiSig', self.multisig_address)
    
    def test_is_spender(self):
        self.assertTrue(self.reserve_wrapper.is_spender(self.reserve_spender_multisig_wrapper.address))
    
    def test_two_spenders_req_confirm_gold(self):
        self.reserve_wrapper._contract.functions.addSpender(self.kit.w3.eth.accounts[0])

        from_block = self.kit.w3.eth.blockNumber
        value_transfer = 10
        tx = self.reserve_wrapper.transfer_gold(self.other_reserve_address, value_transfer)
        tx_abi = self.reserve_wrapper._contract.encodeABI(fn_name="transferGold", args=[self.other_reserve_address, value_transfer])
        multisig_tx = self.reserve_spender_multisig_wrapper.submit_or_confirm_transaction(self.reserve_wrapper.address, tx_abi)
        submission_event = self.reserve_spender_multisig_wrapper._contract.events.Submission.getLogs(fromBlock=from_block)
        confirmation_event = self.reserve_spender_multisig_wrapper._contract.events.Confirmation.getLogs(fromBlock=from_block)
        execution_event = self.reserve_spender_multisig_wrapper._contract.events.Execution.getLogs(fromBlock=from_block)

        self.assertTrue(submission_event)
        self.assertTrue(confirmation_event)
        self.assertFalse(execution_event)

        from_block = self.kit.w3.eth.blockNumber
        tx2 = self.reserve_wrapper.transfer_gold(self.other_reserve_address, value_transfer)
        multisig_tx = self.reserve_spender_multisig_wrapper.submit_or_confirm_transaction(self.reserve_wrapper.address, tx_abi)
        submission_event = self.reserve_spender_multisig_wrapper._contract.events.Submission.getLogs(fromBlock=from_block)
        confirmation_event = self.reserve_spender_multisig_wrapper._contract.events.Confirmation.getLogs(fromBlock=from_block)
        execution_event = self.reserve_spender_multisig_wrapper._contract.events.Execution.getLogs(fromBlock=from_block)

        self.assertFalse(submission_event)
        self.assertTrue(confirmation_event)
        self.assertTrue(execution_event)
    
    @unittest.expectedFailure
    def test_does_not_transfer_if_not_spender(self):
        value_transfer = 10000000
        tx = self.reserve_wrapper.transfer_gold(self.other_reserve_address, value_transfer)
        tx_abi = self.reserve_wrapper._contract.encodeABI(fn_name="transferGold", args=[self.other_reserve_address, value_transfer])
        self.kit.w3.eth.defaultAccount = self.other_spender
        self.kit.wallet_change_account = self.other_spender
        multisig_tx = self.reserve_spender_multisig_wrapper.submit_or_confirm_transaction(self.reserve_wrapper.address, tx_abi)
