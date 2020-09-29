import time
import unittest
import json

from web3 import Web3

from celo_sdk.kit import Kit
from celo_sdk.tests import test_data


class TestGovernanceWrapper(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.kit = Kit('http://localhost:8544')
        self.governance_wrapper = self.kit.base_wrapper.create_and_get_contract_by_name(
            'Governance')
        self.governance_approve_multisig_wrapper = self.kit.base_wrapper.create_and_get_contract_by_name(
            'MultiSig', self.governance_wrapper.get_approver())
        self.locked_gold_wrapper = self.kit.base_wrapper.create_and_get_contract_by_name(
            'LockedGold')
        self.accounts_wrapper = self.kit.base_wrapper.create_and_get_contract_by_name(
            'Accounts')
        self.gold_token_wrapper = self.kit.base_wrapper.create_and_get_contract_by_name('GoldToken')
        self.registry_contract = self.kit.base_wrapper.registry.registry

        self.kit.wallet.sign_with_provider = True
        for _, v in test_data.deriv_pks.items():
            self.kit.wallet_add_new_key = v
        self.accounts = self.kit.w3.eth.accounts

        with open('celo_sdk/tests/dev_net_conf.json') as file:
            data = json.load(file)
            self.exc_config = data['governance']

        self.one_sec = 1000
        self.min_deposit = self.kit.w3.toWei(
            self.exc_config['minDeposit'], 'ether')
        self.one_gold = self.kit.w3.toWei(1, 'ether')

        for account in self.accounts[:4]:
            self.kit.w3.eth.defaultAccount = account
            self.accounts_wrapper.create_account()
            self.locked_gold_wrapper.lock({'value': self.one_gold})

        self.repoints = [['Random', '0x0000000000000000000000000000000000000001'], [
            'Escrow', '0x0000000000000000000000000000000000000002']]
        self.proposal_id = 1
        self.proposal = []
        for repoint in self.repoints:
            self.proposal.append({'value': 0, 'to': '0x000000000000000000000000000000000000ce10',
                                  'input': self.registry_contract.encodeABI(fn_name="setAddressFor", args=[repoint[0], repoint[1]])})

    def test_get_config(self):
        config = self.governance_wrapper.get_config()

        self.assertEqual(config['concurency_proposals'],
                         self.exc_config['concurrentProposals'])
        self.assertEqual(config['dequeue_frequency'],
                         self.exc_config['dequeueFrequency'])
        self.assertEqual(config['min_deposit'], self.exc_config['minDeposit'])
        self.assertEqual(config['queue_expiry'],
                         self.exc_config['queueExpiry'])
        self.assertEqual(config['stage_duration']['approval'],
                         self.exc_config['approvalStageDuration'])
        self.assertEqual(config['stage_duration']['referendum'],
                         self.exc_config['referendumStageDuration'])
        self.assertEqual(config['stage_duration']['execution'],
                         self.exc_config['executionStageDuration'])

    def propose_fn(self):
        self.governance_wrapper.propose(self.proposal, 'URL', {'value': self.min_deposit})
    
    def upvote_fn(self, upvoter: str, should_time_travel: bool = True):
        self.kit.w3.eth.defaultAccount = upvoter
        self.kit.wallet_change_account = upvoter
        tx = self.governance_wrapper.upvote(self.proposal_id, upvoter)
        if should_time_travel:
            self.governance_wrapper.dequeue_proposals_if_ready()
    
    def approve_fn(self):
        self.kit.w3.eth.defaultAccount = self.accounts[0]
        self.kit.wallet_change_account = self.accounts[0]
        tx = self.governance_wrapper.approve(self.proposal_id)
        tx_abi = self.governance_wrapper._contract.encodeABI(fn_name="approve", args=[self.proposal_id])
        multisig_tx = self.governance_approve_multisig_wrapper.submit_or_confirm_transaction(self.governance_wrapper.address, tx_abi)
    
    def vote_fn(self, voter: str):
        self.kit.w3.eth.defaultAccount = voter
        self.kit.wallet_change_account = voter
        tx = self.governance_wrapper.vote(self.proposal_id, 'Yes')
    
    def test_propose(self):
        self.kit.w3.eth.defaultAccount = self.accounts[0]
        self.propose_fn()

        proposal_record = self.governance_wrapper.get_proposal_record(self.proposal_id)

        self.assertEqual(proposal_record['metadata']['proposer'], self.accounts[0])
        self.assertEqual(proposal_record['metadata']['transaction_count'], len(self.proposal))
        self.assertEqual(proposal_record['proposal'], self.proposal)
        self.assertEqual(proposal_record['stage'], 'Queued')
    
    def test_upvote(self):
        self.propose_fn()
        self.upvote_fn(self.accounts[1], False)

        vote_weight = self.governance_wrapper.get_vote_weight(self.accounts[1])
        upvotes = self.governance_wrapper.get_upvotes(self.proposal_id)

        self.assertEqual(upvotes, vote_weight)
        self.assertEqual(upvotes, self.one_gold)
    
    def test_revoke_upvote(self):
        self.propose_fn()
        self.upvote_fn(self.accounts[1], False)

        before = self.governance_wrapper.get_upvotes(self.proposal_id)
        upvote_record = self.governance_wrapper.get_upvote_record(self.accounts[1])

        self.kit.w3.eth.defaultAccount = self.accounts[1]
        self.kit.wallet_change_account = self.accounts[1]

        tx = self.governance_wrapper.revoke_upvote(self.accounts[1])

        after = self.governance_wrapper.get_upvotes(self.proposal_id)

        self.assertEqual(after, before - upvote_record['upvotes'])
    
    def test_approve(self):
        self.propose_fn()
        self.upvote_fn(self.accounts[1])
        self.approve_fn()

        approved = self.governance_wrapper.is_approved(self.proposal_id)

        self.assertTrue(approved)
    
    def test_vote(self):
        self.propose_fn()
        self.upvote_fn(self.accounts[1])
        self.approve_fn()
        self.vote_fn(self.accounts[2])

        vote_weight = self.governance_wrapper.get_vote_weight(self.accounts[2])
        yes_votes = self.governance_wrapper.get_votes(self.proposal_id)['Yes']

        self.assertEqual(yes_votes, vote_weight)
    
    def test_execute(self):
        self.propose_fn()
        self.upvote_fn(self.accounts[1])
        self.approve_fn()
        self.vote_fn(self.accounts[2])

        tx = self.governance_wrapper.execute(self.proposal_id)

        exists = self.governance_wrapper.proposal_exists(self.proposal_id)

        self.assertFalse(exists)
    
    def test_get_voter(self):
        self.propose_fn()
        self.upvote_fn(self.accounts[1])
        self.approve_fn()
        self.vote_fn(self.accounts[2])

        proposer = self.governance_wrapper.get_voter(self.accounts[0])

        self.assertEqual(proposer['refunded_deposits'], self.min_deposit)

        upvoter = self.governance_wrapper.get_voter(self.accounts[1])
        expected_upvote_record = {'proposal_id': self.proposal_id, 'upvotes': self.one_gold}

        self.assertEqual(upvoter['upvote'], expected_upvote_record)

        voter = self.governance_wrapper.get_voter(self.accounts[2])
        expected_vote_record = {'proposal_id': self.proposal_id, 'votes': self.one_gold, 'value': 'Yes'}

        self.assertEqual(voter['votes'][0], expected_vote_record)
