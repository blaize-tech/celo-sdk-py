import time
import unittest
import random

from web3 import Web3
from eth_keys import keys

from sdk.kit import Kit
from sdk.tests import test_data


class TestAccountsWrapper(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        # https://alfajores-forno.celo-testnet.org
        # http://localhost:8545
        self.kit = Kit('https://alfajores-forno.celo-testnet.org')
        self.accounts_wrapper = self.kit.base_wrapper.create_and_get_contract_by_name(
            'Accounts')
        self.kit.wallet_add_new_key = test_data.pk1
        self.kit.wallet_add_new_key = test_data.pk2

        self.validators_contract = self.kit.base_wrapper.create_and_get_contract_by_name(
            'Validators')
        self.locked_gold_contract = self.kit.base_wrapper.create_and_get_contract_by_name(
            'LockedGold')

        self.min_locked_gold_value = self.kit.w3.toWei(10000, 'ether')

        self.bls_public_key = '0x4fa3f67fc913878b068d1fa1cdddc54913d3bf988dbe5a36a20fa888f20d4894c408a6773f3d7bde11154f2a3076b700d345a42fd25a0e5e83f4db5586ac7979ac2053cd95d8f2efd3e959571ceccaa743e02cf4be3f5d7aaddb0b06fc9aff00'
        self.bls_pop = '0xcdb77255037eb68897cd487fdd85388cbda448f617f874449d4b11588b0b7ad8ddc20d9bb450b513bb35664ea3923900'

    def test_authorize_validator_key_not_validator(self):
        accounts = list(self.kit.wallet.accounts.values())[1:]

        account = accounts[0]
        signer = accounts[1]

        self.kit.wallet_change_account = account.address

        self.accounts_wrapper.create_account()

        sig = self.get_parsed_signature_of_address(account.address, signer.address)

        print(self.accounts_wrapper.authorize_validator_signer(signer.address, sig))

    # def test_authorize_validator_key_validator(self):
    #     accounts = list(self.kit.wallet.accounts.values())[1:]

    #     account = accounts[0]
    #     signer = accounts[1]

    #     self.kit.wallet_change_account = account.address

    #     self.accounts_wrapper.create_account()

    #     self.setup_validator(account.address)

    #     sig = self.get_parsed_signature_of_address(account.address, signer.address)

    #     print(self.accounts_wrapper.authorize_validator_signer(signer.address, sig))

    # def test_authorize_validator_key_change_bls_key(self):
    #     hex_characters = '0123456789abcdef'
    #     hex_sample = [random.choice(hex_characters) for _ in range(96)]
    #     new_bls_public_key = '0x'+''.join(hex_sample)

    #     hex_sample = [random.choice(hex_characters) for _ in range(48)]
    #     new_bls_pop = '0x'+''.join(hex_sample)

    #     accounts = list(self.kit.wallet.accounts.values())[1:]

    #     account = accounts[0]
    #     signer = accounts[1]

    #     self.accounts_wrapper.create_account()

    #     self.setup_validator(account.address)

    #     sig = self.get_parsed_signature_of_address(account.address, signer.address)

    #     print(self.accounts_wrapper.authorize_validator_signer_and_bls(signer.address, sig, new_bls_public_key, new_bls_pop))

    # def test_set_wallet_address_to_caller(self):
    #     accounts = list(self.kit.wallet.accounts.values())[1:]

    #     self.accounts_wrapper.create_account()
    #     print(self.accounts_wrapper.set_wallet_address(accounts[0].address))

    # def test_set_wallet_address_to_different_address(self):
    #     accounts = list(self.kit.wallet.accounts.values())[1:]

    #     account = accounts[0]
    #     signer = accounts[1]

    #     self.accounts_wrapper.create_account()

    #     signature = self.accounts_wrapper.generate_proof_of_key_possession(account.address, signer.address)

    #     print(self.accounts_wrapper.set_wallet_address(signer.address, signature))

    # def test_set_wallet_address_without_signature(self):
    #     """
    #     Should fail
    #     """
    #     accounts = list(self.kit.wallet.accounts.values())[1:]
    #     print(self.accounts_wrapper.set_wallet_address(accounts[1].address))

    # def register_account_with_locked_gold(self, account: str):
    #     if not self.accounts_wrapper.is_account(account):
    #         _ = self.accounts_wrapper.create_account({'from': account})
    #     _ = self.locked_gold_contract.lock(
    #         {'from': account, 'value': self.min_locked_gold_value})

    def get_parsed_signature_of_address(self, address: str, signer: 'Account object') -> 'Signature object':
        message = self.kit.w3.soliditySha3(['address'], [address]).hex()
        signature = self.kit.wallet.active_account.signHash(message)
        return signature

    # def setup_validator(self, validator_account: str):
    #     """
    #     validator_account should be an address of active account in wallet now
    #     """
    #     self.register_account_with_locked_gold(validator_account)
    #     priv_key = keys.PrivateKey(self.kit.wallet.active_account.privateKey)
    #     pub_key = priv_key.public_key
    #     _ = self.validators_contract.register_validator(pub_key, self.bls_public_key, self.bls_pop)
