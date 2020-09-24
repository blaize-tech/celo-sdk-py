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
        self.kit.wallet_add_new_key = test_data.pk2

        accounts = list(self.kit.wallet.accounts.values())
        self.other_reserve_address = accounts[0]
        self.other_spender = accounts[1]

        self.spenders = self.reserve_wrapper.get_spenders()
        # assumes that the multisig is the most recent spender in the spenders array
        self.multisig_address = self.spenders[-1] if len(self.spenders) > 0 else ''
        self.reserve_spender_multisig_wrapper = self.kit.base_wrapper.create_and_get_contract_by_name('MultiSig', self.multisig_address)
    
    def test_is_spender(self):
        self.assertTrue(self.reserve_wrapper.is_spender(self.reserve_spender_multisig_wrapper.address))
    
    def test_two_spenders_req_confirm_gold(self):
        from_block = self.kit.w3.eth.blockNumber
        value_transfer = 1
        tx = self.reserve_wrapper.transfer_gold(self.other_reserve_address.address, value_transfer)
        tx_abi = self.reserve_wrapper._contract.encodeABI(fn_name="transferGold", args=[self.other_reserve_address.address, value_transfer])
        multisig_tx = self.reserve_spender_multisig_wrapper.submit_or_confirm_transaction(self.reserve_wrapper.address, tx_abi)
        time.sleep(3)
        submission_event = self.reserve_spender_multisig_wrapper._contract.events.Submission.getLogs(fromBlock=from_block)
        confirmation_event = self.reserve_spender_multisig_wrapper._contract.events.Confirmation.getLogs(fromBlock=from_block)
        execution_event = self.reserve_spender_multisig_wrapper._contract.events.Execution.getLogs(fromBlock=from_block)

        self.assertTrue(submission_event)
        self.assertTrue(confirmation_event)
        self.assertFalse(execution_event)

        from_block = self.kit.w3.eth.blockNumber
        tx2 = self.reserve_wrapper.transfer_gold(self.other_reserve_address.address, value_transfer)
        multisig_tx = self.reserve_spender_multisig_wrapper.submit_or_confirm_transaction(self.reserve_wrapper.address, tx_abi)
        time.sleep(3)
        submission_event = self.reserve_spender_multisig_wrapper._contract.events.Submission.getLogs(fromBlock=from_block)
        confirmation_event = self.reserve_spender_multisig_wrapper._contract.events.Confirmation.getLogs(fromBlock=from_block)
        execution_event = self.reserve_spender_multisig_wrapper._contract.events.Execution.getLogs(fromBlock=from_block)

        self.assertFalse(submission_event)
        self.assertTrue(confirmation_event)
        self.assertTrue(execution_event)
    
    @unittest.expectedFailure
    def test_does_not_transfer_if_not_spender(self):
        value_transfer = 1
        tx = self.reserve_wrapper.transfer_gold(self.other_reserve_address.address, value_transfer)
        tx_abi = self.reserve_wrapper._contract.encodeABI(fn_name="transferGold", args=[self.other_reserve_address.address, value_transfer])
        multisig_tx = self.reserve_spender_multisig_wrapper.submit_or_confirm_transaction(self.reserve_wrapper.address, tx_abi, parameters = {'from': self.other_spender.address})
