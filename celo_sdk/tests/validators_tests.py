import time
import unittest
import json
import random

from web3 import Web3
from eth_keys import keys

from celo_sdk.kit import Kit
from celo_sdk.tests import test_data


class TestValidatorsWrapper(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.kit = Kit('http://localhost:8544')
        self.validators_wrapper = self.kit.base_wrapper.create_and_get_contract_by_name(
            'Validators')
        self.kit.wallet.sign_with_provider = True
        for _, v in test_data.deriv_pks.items():
            self.kit.wallet_add_new_key = v
        self.accounts = self.kit.w3.eth.accounts

        with open('celo_sdk/tests/dev_net_conf.json') as file:
            data = json.load(file)
            self.net_config = data

        self.min_locked_gold_value = self.kit.w3.toWei(10000, 'ether')
        self.bls_pub_key = '0x4fa3f67fc913878b068d1fa1cdddc54913d3bf988dbe5a36a20fa888f20d4894c408a6773f3d7bde11154f2a3076b700d345a42fd25a0e5e83f4db5586ac7979ac2053cd95d8f2efd3e959571ceccaa743e02cf4be3f5d7aaddb0b06fc9aff00'
        self.bls_pop = '0xcdb77255037eb68897cd487fdd85388cbda448f617f874449d4b11588b0b7ad8ddc20d9bb450b513bb35664ea3923900'

        self.locked_gold_wrapper = self.kit.base_wrapper.create_and_get_contract_by_name('LockedGold')
        self.accounts_wrapper = self.kit.base_wrapper.create_and_get_contract_by_name('Accounts')
    
    def register_account_with_locked_gold(self, account: str, value: int):
        if not self.accounts_wrapper.is_account(account):
            self.accounts_wrapper.create_account()
        self.locked_gold_wrapper.lock({'value': value})
    
    def setup_group(self, group_account: str, members: int = 1):
        self.kit.w3.eth.defaultAccount = group_account
        self.kit.wallet_change_account = group_account
        self.register_account_with_locked_gold(group_account, self.min_locked_gold_value * members)
        time.sleep(3)
        self.validators_wrapper.register_validator_group(0.1)
    
    def setup_validator(self, validator_account: str):
        self.kit.w3.eth.defaultAccount = validator_account
        self.kit.wallet_change_account = validator_account
        self.register_account_with_locked_gold(validator_account, self.min_locked_gold_value)
        priv_key = keys.PrivateKey(self.kit.wallet.active_account.privateKey)
        pub_key = priv_key.public_key
        _ = self.validators_wrapper.register_validator(pub_key, self.bls_pub_key, self.bls_pop)
    
    def test_register_validator_group(self):
        group_account = self.accounts[0]
        self.setup_group(group_account)
        time.sleep(3)

        self.assertTrue(self.validators_wrapper.is_validator_group(group_account))
    
    def test_register_validator(self):
        validator_account = self.accounts[1]
        self.setup_validator(validator_account)
        time.sleep(3)

        self.assertTrue(self.validators_wrapper.is_validator(validator_account))
    
    def test_add_member(self):
        group_account = self.accounts[0]
        validator_account = self.accounts[1]
        self.setup_group(group_account)
        self.setup_validator(validator_account)
        self.kit.w3.eth.defaultAccount = validator_account
        self.kit.wallet_change_account = validator_account
        self.validators_wrapper.affiliate(group_account)
        self.kit.w3.eth.defaultAccount = group_account
        self.kit.wallet_change_account = group_account
        self.validators_wrapper.add_member(group_account, validator_account)

        members = self.validators_wrapper.get_validator_group(group_account)['members']

        self.assertTrue(validator_account in members)
    
    def test_set_next_commission_update(self):
        group_account = self.accounts[0]
        self.setup_group(group_account)
        self.kit.w3.eth.defaultAccount = group_account
        self.kit.wallet_change_account = group_account
        self.validators_wrapper.set_next_commission_update(0.2)
        commission = self.validators_wrapper.get_validator_group(group_account)['next_commission']

        self.assertEqual(commission, 0.2)
    
    def test_update_commission(self):
        group_account = self.accounts[0]
        self.setup_group(group_account)
        self.kit.w3.eth.defaultAccount = group_account
        self.kit.wallet_change_account = group_account
        self.validators_wrapper.set_next_commission_update(0.2)
        time.sleep(6)
        self.validators_wrapper.update_commission({'from': group_account})

        commission = self.validators_wrapper.get_validator_group(group_account)['commission']

        self.assertEqual(commission, 0.2)
    
    def test_get_group_affiliates(self):
        group_account = self.accounts[0]
        validator_account = self.accounts[1]
        self.setup_group(group_account)
        self.setup_validator(validator_account)
        self.kit.w3.eth.defaultAccount = validator_account
        self.kit.wallet_change_account = validator_account
        self.validators_wrapper.affiliate(group_account)

        group = self.validators_wrapper.get_validator_group(group_account)

        self.assertTrue(validator_account in group['affiliates'])
    
    def test_move_last_to_first(self):
        group_account = self.accounts[0]
        self.setup_group(group_account, 2)

        validator1 = self.accounts[1]
        validator2 = self.accounts[2]

        for validator in [validator1, validator2]:
            self.setup_validator(validator)
            self.kit.w3.eth.defaultAccount = validator
            self.kit.wallet_change_account = validator
            self.validators_wrapper.affiliate(group_account)
            self.kit.w3.eth.defaultAccount = group_account
            self.kit.wallet_change_account = group_account
            self.validators_wrapper.add_member(group_account, validator)
        
        members = self.validators_wrapper.get_validator_group(group_account)['members']

        self.assertEqual(members, [validator1, validator2])

        self.kit.w3.eth.defaultAccount = group_account
        self.kit.wallet_change_account = group_account
        self.validators_wrapper.reorder_member(group_account, validator2, 0)

        members_after = self.validators_wrapper.get_validator_group(group_account)['members']

        self.assertEqual(members_after, [validator2, validator1])
    
    def test_move_first_to_last(self):
        group_account = self.accounts[0]
        self.setup_group(group_account, 2)

        validator1 = self.accounts[1]
        validator2 = self.accounts[2]

        for validator in [validator1, validator2]:
            self.setup_validator(validator)
            self.kit.w3.eth.defaultAccount = validator
            self.kit.wallet_change_account = validator
            self.validators_wrapper.affiliate(group_account)
            self.kit.w3.eth.defaultAccount = group_account
            self.kit.wallet_change_account = group_account
            self.validators_wrapper.add_member(group_account, validator)
        
        members = self.validators_wrapper.get_validator_group(group_account)['members']

        self.assertEqual(members, [validator1, validator2])

        self.kit.w3.eth.defaultAccount = group_account
        self.kit.wallet_change_account = group_account
        self.validators_wrapper.reorder_member(group_account, validator1, 1)

        members_after = self.validators_wrapper.get_validator_group(group_account)['members']

        self.assertEqual(members_after, [validator2, validator1])
    
    def test_address_normalization(self):
        group_account = self.accounts[0]
        self.setup_group(group_account, 2)

        validator1 = self.accounts[1]
        validator2 = self.accounts[2]

        for validator in [validator1, validator2]:
            self.setup_validator(validator)
            self.kit.w3.eth.defaultAccount = validator
            self.kit.wallet_change_account = validator
            self.validators_wrapper.affiliate(group_account)
            self.kit.w3.eth.defaultAccount = group_account
            self.kit.wallet_change_account = group_account
            self.validators_wrapper.add_member(group_account, validator)
        
        members = self.validators_wrapper.get_validator_group(group_account)['members']

        self.assertEqual(members, [validator1, validator2])

        self.kit.w3.eth.defaultAccount = group_account
        self.kit.wallet_change_account = group_account
        self.validators_wrapper.reorder_member(group_account, validator2, 0)

        members_after = self.validators_wrapper.get_validator_group(group_account)['members']

        self.assertEqual(members_after, [validator2, validator1])
