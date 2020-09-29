import random
import time
import unittest

from celo_sdk.celo_account.account import Account
from celo_sdk.celo_account.messages import encode_defunct
from celo_sdk.kit import Kit
from celo_sdk.tests import test_data
from celo_sdk.utils import utils
from eth_keys import keys
from hexbytes import HexBytes
from web3 import Web3


class TestAccountsWrapper(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        # https://alfajores-forno.celo-testnet.org
        # http://localhost:8545
        self.kit = Kit('http://localhost:8544')
        self.accounts_wrapper = self.kit.base_wrapper.create_and_get_contract_by_name(
            'Accounts')
        self.kit.wallet.sign_with_provider = True
        for _, v in test_data.deriv_pks.items():
            self.kit.wallet_add_new_key = v

        self.validators_contract = self.kit.base_wrapper.create_and_get_contract_by_name(
            'Validators')
        self.locked_gold_contract = self.kit.base_wrapper.create_and_get_contract_by_name(
            'LockedGold')

        self.min_locked_gold_value = self.kit.w3.toWei(10000, 'ether')

        self.bls_public_key = '0x4fa3f67fc913878b068d1fa1cdddc54913d3bf988dbe5a36a20fa888f20d4894c408a6773f3d7bde11154f2a3076b700d345a42fd25a0e5e83f4db5586ac7979ac2053cd95d8f2efd3e959571ceccaa743e02cf4be3f5d7aaddb0b06fc9aff00'
        self.bls_pop = '0xcdb77255037eb68897cd487fdd85388cbda448f617f874449d4b11588b0b7ad8ddc20d9bb450b513bb35664ea3923900'
    
    def test_create_acc(self):
        accounts = self.kit.w3.eth.accounts
        self.kit.wallet_change_account = accounts[1]
        self.kit.wallet.sign_with_provider = True
        print(self.accounts_wrapper.create_account())

    def test_pub_key_recovering(self):
        accounts = self.kit.w3.eth.accounts

        account = accounts[0]
        signer = accounts[1]
        
        self.kit.w3.eth.defaultAccount = signer
        self.kit.wallet_change_account = signer

        message = self.kit.w3.soliditySha3(['address'], [signer]).hex()
        message = encode_defunct(hexstr=message)
        signature = self.kit.wallet.active_account.sign_message(message)

        self.assertEqual(Account.recover_hash_to_pub(message, vrs=signature.vrs).to_hex(), test_data.recovered_pub_key)

    def test_authorize_validator_key_not_validator(self):
        accounts = self.kit.w3.eth.accounts

        account = accounts[0]
        signer = accounts[1]

        self.kit.w3.eth.defaultAccount = account
        self.kit.wallet_change_account = account

        self.accounts_wrapper.create_account()

        sig = self.get_parsed_signature_of_address(account, signer)

        self.assertTrue(self.accounts_wrapper.authorize_validator_signer(signer, sig))

    def test_authorize_validator_key_validator(self):
        accounts = self.kit.w3.eth.accounts

        account = accounts[0]
        signer = accounts[1]

        self.kit.wallet_change_account = account
        self.kit.w3.eth.defaultAccount = account

        self.accounts_wrapper.create_account()

        self.setup_validator(account)

        self.kit.wallet_change_account = signer
        self.kit.w3.eth.defaultAccount = signer

        sig = self.get_parsed_signature_of_address(account, signer)

        self.kit.wallet_change_account = account
        self.kit.w3.eth.defaultAccount = account

        self.assertTrue(self.accounts_wrapper.authorize_validator_signer(signer.address, sig))

    def test_authorize_validator_key_change_bls_key(self):
        hex_characters = '0123456789abcdef'
        hex_sample = [random.choice(hex_characters) for _ in range(96)]
        new_bls_public_key = '0x'+''.join(hex_sample)

        hex_sample = [random.choice(hex_characters) for _ in range(48)]
        new_bls_pop = '0x'+''.join(hex_sample)

        accounts = list(self.kit.wallet.accounts.values())[1:]

        account = accounts[0]
        signer = accounts[1]

        self.accounts_wrapper.create_account()

        self.setup_validator(account)

        sig = self.get_parsed_signature_of_address(account, signer)

        self.assertTrue(self.accounts_wrapper.authorize_validator_signer_and_bls(signer.address, sig, new_bls_public_key, new_bls_pop))

    def test_set_wallet_address_to_caller(self):
        accounts = list(self.kit.wallet.accounts.values())[1:]

        self.accounts_wrapper.create_account()
        self.assertTrue(self.accounts_wrapper.set_wallet_address(accounts[0]))

    def test_set_wallet_address_to_different_address(self):
        accounts = list(self.kit.wallet.accounts.values())[1:]

        account = accounts[0]
        signer = accounts[1]

        self.accounts_wrapper.create_account()

        signature = self.accounts_wrapper.generate_proof_of_key_possession(account, signer)

        self.assertTrue(self.accounts_wrapper.set_wallet_address(signer, signature))

    def test_set_wallet_address_without_signature(self):
        """
        Should fail
        """
        accounts = list(self.kit.wallet.accounts.values())[1:]
        self.assertTrue(self.accounts_wrapper.set_wallet_address(accounts[1]))

    def register_account_with_locked_gold(self, account: str):
        if not self.accounts_wrapper.is_account(account):
            _ = self.accounts_wrapper.create_account({'from': account})
        _ = self.locked_gold_contract.lock(
            {'from': account, 'value': self.min_locked_gold_value})

    def get_parsed_signature_of_address(self, address: str, signer: 'Account object') -> 'Signature object':
        self.kit.w3.eth.defaultAccount = signer
        self.kit.wallet_change_account = signer

        message = self.kit.w3.soliditySha3(['address'], [address]).hex()
        message = encode_defunct(hexstr=message)
        signature = self.kit.wallet.active_account.sign_message(message)

        self.kit.w3.eth.defaultAccount = address
        self.kit.wallet_change_account = address
        return signature

    def setup_validator(self, validator_account: str):
        """
        validator_account should be an address of active account in wallet now
        """
        self.register_account_with_locked_gold(validator_account)
        priv_key = keys.PrivateKey(self.kit.wallet.active_account.privateKey)
        pub_key = priv_key.public_key
        _ = self.validators_contract.register_validator(pub_key, self.bls_public_key, self.bls_pop)
