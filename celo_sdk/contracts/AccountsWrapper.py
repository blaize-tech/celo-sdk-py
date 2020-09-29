import sys

from celo_sdk.celo_account.account import Account
from celo_sdk.celo_account.messages import encode_defunct
from celo_sdk.celo_account.datastructures import SignedMessage
from celo_sdk.contracts.base_wrapper import BaseWrapper
from celo_sdk.registry import Registry
from celo_sdk.utils import hash_utils

from web3 import Web3


class Accounts(BaseWrapper):
    """
    Contract for handling deposits needed for voting

    Attributes:
        web3: Web3
            Web3 object
        registry: Registry
            Registry object
        address: str
            Contract's address
        abi: list
            Contract's ABI
        wallet: Wallet
            Wallet object to sign transactions
    """

    def __init__(self, web3: Web3, registry: Registry, address: str, abi: list, wallet: 'Wallet' = None):
        super().__init__(web3, registry, wallet=wallet)
        self.web3 = web3
        self.address = address
        self._contract = self.web3.eth.contract(self.address, abi=abi)
        self.__wallet = wallet

    def create_account(self, parameters: dict = None) -> str:
        """
        Creates an account

        Returns:
            Transaction hash
        """
        func_call = self._contract.functions.createAccount()
        return self.__wallet.send_transaction(func_call, parameters=parameters)

    def get_attestation_signer(self, account: str) -> str:
        """
        Returns the attestation signer for the specified account

        Parameters:
            account: str
                The address of the account
        Returns:
            The address with which the account can vote
        """
        return self._contract.functions.getAttestationSigner().call()

    def has_authorized_attestation_signer(self, account: str) -> str:
        """
        Returns if the account has authorized an attestation signer

        Parameters:
            account: str
                The address of the account
        Returns:
            If the account has authorized an attestation signer
        """
        return self._contract.functions.hasAuthorizedAttestationSigner().call()

    def get_vote_signer(self, account: str) -> str:
        """
        Returns the vote signer for the specified account

        Parameters:
            account: str
                The address of the account
        Returns:
            The address with which the account can vote
        """
        return self._contract.functions.getVoteSigner().call()

    def get_validator_signer(self, account: str) -> str:
        """
        Returns the validator signer for the specified account

        Parameters:
            account: str
                The address of the account
        Returns:
            The address with which the account can register a validator or group
        """
        return self._contract.functions.getValidatorSigner().call()

    def vote_signer_to_account(self, signer: str) -> str:
        """
        Returns the account address given the signer for voting

        Parameters:
            signer: str
                Address that is authorized to sign the tx as voter
        Returns:
            The Account address
        """
        return self._contract.functions.voteSignerToAccount().call()

    def validator_signer_to_account(self, signer: str) -> str:
        """
        Returns the account address given the signer for validating

        Parameters:
            signer: str
                Address that is authorized to sign the tx as validator
        Returns:
            The Account address
        """
        return self._contract.functions.validatorSignerToAccount().call()

    def signer_to_account(self, signer: str) -> str:
        """
        Returns the account associated with `signer`

        Parameters:
            signer: str
                The address of the account or previously authorized signer
        Returns:
            The associated account
        """
        return self._contract.functions.signerToAccount().call()

    def is_account(self, account: str) -> bool:
        """
        Check if an account already exists

        Parameters:
            account: str
                The address of the account
        Returns:
            Returns `true` if account exists. Returns `false` otherwise
        """
        return self._contract.functions.isAccount(account).call()

    def is_signer(self, address: str) -> bool:
        """
        Check if an address is a signer address

        Parameters:
            address: str
                The address of the account
        Returns:
            Returns `true` if account exists. Returns `false` otherwise
        """
        return self._contract.functions.isAuthorizedSigner().call()

    def get_current_signers(self, address: str) -> dict:
        vote_signer = self.get_vote_signer(address)
        validator_signer = self.get_validator_signer(address)
        attestation_signer = self.get_attestation_signer(address)

        return {
            'vote_signer': vote_signer,
            'validator_signer': validator_signer,
            'attestation_signer': attestation_signer
        }

    def get_account_summary(self, account: str) -> dict:
        name = self.get_name(account)
        vote_signer = self.get_vote_signer(account)
        validator_signer = self.get_validator_signer(account)
        attestation_signer = self.get_attestation_signer(account)
        metadata_url = self.get_metadata_url(account)
        wallet_address = self.get_wallet_address(account)
        data_encryption_key = self.get_data_encryption_key(account)

        return {
            'address': account,
            'name': name,
            'authorized_signers': {
                'vote': vote_signer,
                'validator': validator_signer,
                'attestation': attestation_signer
            },
            'metadata_url': metadata_url,
            'wallet': wallet_address,
            'data_encryption_key': data_encryption_key
        }

    def authorize_attestation_signer(self, signer: str, proof_of_signing_key_possession: SignedMessage) -> str:
        """
        Authorize an attestation signing key on behalf of this account to another address

        Parameters:
            signer: str
                The address of the signing key to authorize
            proof_of_signing_key_possession: SignedMessage
                The account address signed by the signer address
        Returns:
            Transaction hash
        """
        func_call = self._contract.functions.authorizeAttestationSigner(
            signer, proof_of_signing_key_possession.v, self.web3.toBytes(proof_of_signing_key_possession.r), self.web3.toBytes(proof_of_signing_key_possession.s))
        return self.__wallet.send_transaction(func_call)

    def authorize_vote_signer(self, signer: str, proof_of_signing_key_possession: SignedMessage) -> str:
        """
        Authorizes an address to sign votes on behalf of the account

        Parameters:
            signer: str
                The address of the vote signing key to authorize
            proof_of_signing_key_possession: SignedMessage
                The account address signed by the signer address
        Returns:
            Transaction hash
        """
        func_call = self._contract.functions.authorizeVoteSigner(
            signer, proof_of_signing_key_possession.v, self.web3.toBytes(proof_of_signing_key_possession.r), self.web3.toBytes(proof_of_signing_key_possession.s))
        return self.__wallet.send_transaction(func_call)

    def authorize_validator_signer(self, signer: str, proof_of_signing_key_possession: SignedMessage) -> str:
        """
        Authorizes an address to sign consensus messages on behalf of the account

        Parameters:
            signer: str
                The address of the signing key to the authorize
            proof_of_signing_key_possession: SignedMessage
                The account address signed by the signer address
        Returns:
            Transaction hash
        """
        validators = self.create_and_get_contract_by_name('Validators')
        account = self.__wallet.active_account.address
        if validators.is_validator(account):
            message = self.web3.soliditySha3(['address'], [account]).hex()
            prefixed_message_hash = hash_utils.hash_message_with_prefix(
                self.web3, message)
            prefixed_message_hash = encode_defunct(hexstr=prefixed_message_hash)
            pub_key = Account.recover_hash_to_pub(prefixed_message_hash, vrs=proof_of_signing_key_possession.vrs).to_hex()
            func_call = self._contract.functions.authorizeValidatorSignerWithPublicKey(
                signer, proof_of_signing_key_possession.v, self.web3.toBytes(proof_of_signing_key_possession.r), self.web3.toBytes(proof_of_signing_key_possession.s), pub_key)
            return self.__wallet.send_transaction(func_call)
        else:
            func_call = self._contract.functions.authorizeValidatorSigner(
                signer, proof_of_signing_key_possession.v, self.web3.toBytes(proof_of_signing_key_possession.r), self.web3.toBytes(proof_of_signing_key_possession.s))
            return self.__wallet.send_transaction(func_call)

    def authorize_validator_signer_and_bls(self, signer: str, proof_of_signing_key_possession: SignedMessage, bls_public_key: str, bls_pop: str) -> str:
        """
        Authorizes an address to sign consensus messages on behalf of the account. Also switch BLS key at the same time

        Parameters:
            signer: str
                The address of the signing key to authorize
            proof_of_signing_key_possession: SignedMessage
                The account address signed by the signer address
            bls_public_key: str
                The BLS public key that the validator is using for consensus, should pass proof of possession, 48 bytes
            bls_pop: str
                The BLS public key proof-of-possession, which consists of a signature on the account address, 96 bytes
        Returns:
            Transaction hash
        """
        account = self.__wallet.active_account.address
        message = self.web3.soliditySha3(['address'], [account]).hex()
        prefixed_message_hash = hash_utils.hash_message_with_prefix(
            self.web3, message)
        prefixed_message_hash = encode_defunct(hexstr=prefixed_message_hash)
        pub_key = Account.recover_hash_to_pub(prefixed_message_hash, vrs=proof_of_signing_key_possession.vrs).to_hex()

        func_call = self._contract.functions.authorizeValidatorSignerWithKeys(signer, proof_of_signing_key_possession.v, self.web3.toBytes(proof_of_signing_key_possession.r),
                     self.web3.toBytes(proof_of_signing_key_possession.s), pub_key, hash_utils.is_leading_with_0x(bls_public_key), hash_utils.is_leading_with_0x(bls_pop))
        return self.__wallet.send_transaction(func_call)

    def generate_proof_of_key_possession(self, account: str, signer: str) -> SignedMessage:
        message = self.web3.soliditySha3(['address'], [account]).hex()
        prefixed_message_hash = hash_utils.hash_message_with_prefix(
            self.web3, message)
        prefixed_message_hash = encode_defunct(hexstr=prefixed_message_hash)
        signer_acc = self.__wallet.accounts[signer]
        signature = signer_acc.sign_message(prefixed_message_hash)
        return signature

    def get_name(self, account: str, block_number: int = None) -> str:
        """
        Returns the set name for the account

        Parameters:
            account: str
                Account address
        """
        if block_number != None:
            return self._contract.functions.getName(account).call(block_number=block_number)
        else:
            return self._contract.functions.getName(account).call()

    def get_data_encryption_key(self, account: str) -> str:
        """
        Returns the set data encryption key for the account

        Parameters:
            account: str
                Account address
        """
        return self._contract.functions.getDataEncryptionKey(account).call()

    def get_wallet_address(self, account: str) -> str:
        """
        Returns the set wallet address for the account

        Parameters:
            account: str
                Account address
        """
        return self._contract.functions.getWalletAddress(account).call()

    def get_metadata_url(self, account: str) -> str:
        """
        Returns the metadataURL for the account

        Parameters:
            account: str
                Account address
        """
        return self._contract.functions.getMetadataURL(account).call()

    def set_account_data_encryption(self, encryption_key: str) -> str:
        """
        Sets the data encryption of the account

        Parameters:
            encryption_key: str
                The key to set
        Returns:
            Transaction hash
        """
        func_call = self._contract.functions.setAccountDataEncryptionKey(
            encryption_key)
        return self.__wallet.send_transaction(func_call)

    def set_account(self, name: str, data_encryption_key: str, wallet_address: str, proof_of_possession: SignedMessage = None) -> str:
        """
        Convenience Setter for the dataEncryptionKey and wallet address for an account

        Parameters:
            name: str
                A string to set as the name of the account
            data_encryption_key: str
                secp256k1 public key for data encryption. Preferably compressed
            wallet_address: str
                The wallet address to set for the account
            proof_of_possession: SignedMessage
                Signature from the wallet address key over the sender's address
        Returns:
            Transaction hash
        """
        if proof_of_possession:
            func_call = self._contract.functions.setAccount(
                name, data_encryption_key, wallet_address, proof_of_possession.v, self.web3.toBytes(proof_of_possession.r), self.web3.toBytes(proof_of_possession.s))
        else:
            func_call = self._contract.functions.setAccount(
                name, data_encryption_key, wallet_address, 0, self.web3.toBytes('0x0'), self.web3.toBytes('0x0'))
        return self.__wallet.send_transaction(func_call)

    def set_name(self, name: str) -> str:
        """
        Sets the name for the account

        Parameters:
            name: str
                The name to set
        Returns:
            Transaction hash
        """
        func_call = self._contract.functions.setName(name)
        return self.__wallet.send_transaction(func_call)

    def set_metadata_url(self, url: str) -> str:
        """
        Sets the metadataURL for the account

        Parameters:
            url: str
                The url to set
        Returns:
            Transaction hash
        """
        func_call = self._contract.functions.setMetadataURL(url)
        return self.__wallet.send_transaction(func_call)

    def set_wallet_address(self, wallet_address: str, proof_of_possession: SignedMessage) -> str:
        """
        Sets the wallet address for the account

        Parameters:
            wallet_address: str
                The address to set
            proof_of_possession: SignedMessage
                Signature as a proof of key possession
        Returns:
            Transaction hash
        """
        if proof_of_possession:
            func_call = self._contract.functions.setWalletAddress(
                wallet_address, proof_of_possession.v, self.web3.toBytes(proof_of_possession.r), self.web3.toBytes(proof_of_possession.s))
        else:
            func_call = self._contract.functions.setWalletAddress(
                wallet_address, 0, self.web3.toBytes('0x0'), self.web3.toBytes('0x0'))
        return self.__wallet.send_transaction(func_call)
