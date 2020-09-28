import sys

from celo_sdk.contracts.base_wrapper import BaseWrapper
from celo_sdk.registry import Registry

from web3 import Web3


class DoubleSigningSlasher(BaseWrapper):
    """
    Contract handling slashing for Validator double-signing

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

    def slashing_incentives(self) -> dict:
        """
        Returns slashing incentives
        """
        func_call = self._contract.functions.slashingIncentives().call()
        return {'reward': func_call[1], 'penalty': func_call[0]}

    def get_block_number_from_header(self, header: str) -> int:
        """
        Parses block number out of header

        Parameters:
            header: str
                RLP encoded header
        Returns:
            Block number
        """
        return self._contract.functions.getBlockNumberFromHeader(header).call()

    def slash_validator(self, validator_address: str, header_a: str, header_b: str) -> str:
        """
        Slash a Validator for double-signing

        Parameters:
            validator_address: str
                Validator to slash
            header_a: str
                First double signed block header
            header_b: str
                Second double signed block header
        Returns:
            Transaction hash
        """
        election_contract = self.create_and_get_contract_by_name('Election')
        validators_contract = self.create_and_get_contract_by_name(
            'Validators')
        validator = validators_contract.get_validator(validator_address)
        block_number = self.get_block_number_from_header(header_a)
        validator_signers = election_contract.get_validator_signers(
            block_number)
        addrs_index = validator_signers.index(validator['signer'])
        return self.slash(addrs_index, header_a, header_b)

    def slash_signer(self, signer_address: str, header_a: str, header_b: str) -> str:
        """
        Slash a Validator for double-signing

        Parameters:
            signer_address: str
                Signer to slash
            header_a: str
                First double signed block header
            header_b: str
                Second double signed block header
        Returns:
            Transaction hash
        """
        election_contract = self.create_and_get_contract_by_name('Election')
        block_number = self.get_block_number_from_header(header_a)
        validator_signers = election_contract.get_validator_signers(
            block_number)
        addrs_index = validator_signers.index(signer_address)
        return self.slash(addrs_index, header_a, header_b)

    def slash(self, signer_index: str, header_a: str, header_b: str) -> str:
        """
        Slash a Validator for double-signing

        Parameters:
            signer_address: str
                Signer to slash
            header_a: str
                First double signed block header
            header_b: str
                Second double signed block header
        Returns:
            Transaction hash
        """
        incentives = self.slashing_incentives()
        block_number = self.get_block_number_from_header(header_a)
        election_contract = self.create_and_get_contract_by_name('Election')
        validators_contract = self.create_and_get_contract_by_name(
            'Validators')
        signer = election_contract.validator_signer_address_from_set(
            signer_index, block_number)
        validator = validators_contract.get_validator_from_signer(signer)
        membership = validators_contract.get_validator_membership_history_index(
            validator, block_number)
        locked_gold_contract = self.create_and_get_contract_by_name(
            'LockedGold')
        slash_validator = locked_gold_contract.compute_initial_parameters_for_slashing(
            validator['address'], incentives['penalty'])
        slash_group = locked_gold_contract.compute_parameters_for_slashing(
            membership['group'], incentives['penalty'], slash_validator['list'])

        func_call = self._contract.functions.slash(signer,  signer_index, header_a, header_b, membership['history_index'], slash_validator[
                                                   'lessers'], slash_validator['greaters'], slash_validator['indices'], slash_group['lessers'], slash_group['greaters'], slash_group['indices'])

        return self.__wallet.send_transaction(func_call)
