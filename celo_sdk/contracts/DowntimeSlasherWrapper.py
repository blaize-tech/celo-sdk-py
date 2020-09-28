import sys

from celo_sdk.contracts.base_wrapper import BaseWrapper
from celo_sdk.registry import Registry

from web3 import Web3


class DowntimeSlasher(BaseWrapper):
    """
    Contract handling slashing for Validator downtime using intervals

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

    def slashable_downtime(self) -> int:
        """
        Returns slashable downtime in blocks

        Returns:
            The number of consecutive blocks before a Validator missing from IBFT consensus
            can be slashed
        """
        return self._contract.functions.slashableDowntime().call()

    def get_config(self) -> dict:
        """
        Returns current configuration parameters
        """
        return {
            'slashable_downtime': self.slashable_downtime(),
            'slashing_incentives': self.slashing_incentives()
        }

    def was_down_for_interval(self, start_block: int, end_block: int, signer_index: int) -> bool:
        """
        Check if a validator appears down in the bitmap for the interval of blocks
        Both start_block and end_block should be part of the same epoch

        Parameters:
            start_block: int
                First block of the interval
            end_block: int
                Last block of the interval
            signer_index: int
                Index of the signer within the validator set
        Returns:
            True if the validator does not appear in the bitmap of the interval
        """
        return self._contract.functions.wasDownForInterval(start_block, end_block, signer_index).call()

    def get_bitmap_for_interval(self, start_block: int, end_block: int) -> str:
        """
        Calculates and returns the signature bitmap for the specified interval
        Similar to the parentSealBitmap of every block (where you have which validators were
        able to sign the previous block), this bitmap shows for that specific interval which
        validators signed at least one block

        Parameters:
            start_block: int
                First block of the interval
            end_block: int
                Last block of the interval
        Returns:
            The signature uptime bitmap for the specified interval
        """
        return self._contract.functions.getBitmapForInterval(start_block, end_block).call()

    def set_bitmap_for_interval(self, start_block: int, end_block: int) -> str:
        """
        Calculates and sets the signature bitmap for the specified interval

        Parameters:
            start_block: int
                First block of the interval
            end_block: int
                Last block of the interval
        Returns:
            Transaction hash
        """
        func_call = self._contract.functions.setBitmapForInterval(
            start_block, end_block)
        return self.__wallet.send_transaction(func_call)

    def is_bitmap_set_for_interval(self, start_block: int, end_block: int) -> bool:
        """
        Shows if the user already called the `setBitmapForInterval` for
        the specific interval

        Parameters:
            start_block: int
                First block of the interval
            end_block: int
                Last block of the interval
        Returns:
            True if the user already called the `setBitmapForInterval` for
            the specific interval
        """
        return self._contract.functions.isBitmapSetForInterval(start_block, end_block)

    def was_validator_down_for_interval(self, validator_or_signer_address: str, start_block: int, end_block: int) -> bool:
        """
        Tests if the given validator or signer did not sign any blocks in the interval

        Parameters:
            validator_or_signer_address: str
                Address of the validator account or signer
            start_block: int
                First block of the interval
            end_block: int
                Last block of the interval
        """
        start_signer_index = self.get_validator_signer_index(
            validator_or_signer_address, start_block)
        return self.was_down_for_interval(start_block, end_block, start_signer_index)

    def was_down_for_intervals(self, start_blocks: list, end_blocks: list, signer_indices: list) -> bool:
        """
        Returns true if the validator did not sign any blocks for the specified overlapping or adjacent

        Parameters:
            start_block: list
                A list of interval start blocks for which signature bitmaps have already
                been set
            end_block: list
                A list of interval end blocks for which signature bitmaps have already
                been set
            signer_indices: list
                Indices of the signer within the validator set for every epoch change
        """
        return self._contract.functions.wasDownForIntervals(start_blocks, end_blocks, signer_indices)

    def was_validator_down(self, validator_or_signer_address: str, start_blocks: list, end_blocks: list) -> bool:
        """
        Returns true if the validator did not sign any blocks for the specified overlapping or adjacent
        intervals

        Parameters:
            validator_or_signer_address: str
                Address of the validator account or signer
            start_block: list
                A list of interval start blocks for which signature bitmaps have already
                been set
            end_block: list
                A list of interval end blocks for which signature bitmaps have already
                been set
        Returns:
            True if the validator signature does not appear in any block within the window
        """
        if len(start_blocks) == 0 or len(start_blocks) != len(end_blocks):
            raise Exception(
                "Start_blocks and end_blocks lists should have at least one element and have the same length")

        validators_contract = self.create_and_get_contract_by_name(
            'Validators')

        window = self.get_slashable_downtime_window(start_blocks[0])

        signer_indices = []

        signer_indices.append(self.get_validator_signer_index(
            validator_or_signer_address, window['start']))
        start_epoch = validators_contract.get_epoch_number_of_block(
            window['start'])
        end_epoch = validators_contract.get_epoch_number_of_block(
            window['end'])

        if start_epoch < end_epoch:
            signer_indices.append(self.get_validator_signer_index(
                validator_or_signer_address, window['end']))

        return self.was_down_for_intervals(start_blocks, end_blocks, signer_indices)

    def get_validator_signer_index(self, validator_or_signer_address: str, block_number: int) -> int:
        """
        Determines the validator signer given an account or signer address and block number

        Parameters:
            validator_or_signer_address: str
                Address of the validator account or signer
            block_number: int
                Block at which to determine the signer index
        """
        accounts_contract = self.create_and_get_contract_by_name('Accounts')
        validators_contract = self.create_and_get_contract_by_name(
            'Validators')
        is_account = accounts_contract.is_account(validator_or_signer_address)
        signer = validators_contract.get_validator(validator_or_signer_address, block_number)[
            'signer'] if is_account else validator_or_signer_address

        election_contract = self.create_and_get_contract_by_name('Election')
        validator_signers = election_contract.get_validator_signers(
            block_number)

        try:
            index = validator_signers.index(signer)
            return index
        except:
            raise Exception(
                f"Validator signer {signer} was not elected at block {block_number}")

    def slash_validator(self, validator_or_signer_address: str, start_blocks: list, end_blocks: list) -> str:
        """
        Returns true if the validator did not sign any blocks for the specified overlapping or adjacent
        intervals

        Parameters:
            validator_or_signer_address: str
                Address of the validator account or signer
            start_block: list
                A list of interval start blocks for which signature bitmaps have already
                been set
            end_block: list
                A list of interval end blocks for which signature bitmaps have already
                been set
        Returns:
            Transaction hash
        """
        if len(start_blocks) == 0 or len(start_blocks) != len(end_blocks):
            raise Exception(
                "Start_blocks and end_blocks lists should have at least one element and have the same length")

        validator_signer_index = self.get_validator_signer_index(
            validator_or_signer_address, start_blocks[0])

        return self.slash_start_signer_index(validator_signer_index, start_blocks, end_blocks)

    def slash_start_signer_index(self, start_signer_index: int, start_blocks: list, end_blocks: list) -> str:
        """
        Returns true if the validator did not sign any blocks for the specified overlapping or adjacent
        intervals

        Parameters:
            start_signer_index: int
                Validator index at the first block
            start_block: list
                A list of interval start blocks for which signature bitmaps have already
                been set
            end_block: list
                A list of interval end blocks for which signature bitmaps have already
                been set
        Returns:
            Transaction hash
        """
        if len(start_blocks) == 0 or len(start_blocks) != len(end_blocks):
            raise Exception(
                "Start_blocks and end_blocks lists should have at least one element and have the same length")

        election_contract = self.create_and_get_contract_by_name('Election')
        validators_contract = self.create_and_get_contract_by_name(
            'Validators')
        signer = election_contract.validator_signer_address_from_set(
            start_signer_index, start_blocks[0])

        window = self.get_slashable_downtime_window(start_blocks[0])
        start_epoch = validators_contract.get_epoch_number_of_block(
            window['start'])
        end_epoch = validators_contract.get_epoch_number_of_block(
            window['end'])

        signer_indices = [start_signer_index]

        if start_epoch < end_epoch:
            validator_signers = election_contract.get_validator_signers(
                window['end'])
            signer_indices.append(validator_signers.index(signer))

        validator = validators_contract.get_validator_from_signer(signer)

        return self.slash(validator, window, start_blocks, end_blocks, signer_indices)

    def slash(self, validator: dict, slashable_window: dict, start_blocks: list, end_blocks: list, signer_indices: list) -> str:
        """
        Slash a Validator for downtime

        Parameters:
            validator: dict
                Validator to slash for downtime
            slashable_window: dict
                Window of the blocks to slash
            start_blocks: list
                A list of interval start blocks for which signature bitmaps have already
                been set
            end_blocks: list
                A list of interval end blocks for which signature bitmaps have already
                been set
            signer_indices: list
        Returns:
            Transaction hash
        """
        incentives = self.slashing_incentives()
        validators_contract = self.create_and_get_contract_by_name(
            'Validators')
        membership = validators_contract.get_validator_membership_history_index(
            validator, slashable_window['start'])

        locked_gold_contract = self.create_and_get_contract_by_name(
            'LockedGold')
        slash_validator = locked_gold_contract.compute_initial_parameters_for_slashing(
            validator['address'], incentives['penalty'])
        slash_group = locked_gold_contract.compute_parameters_for_slashing(
            membership['group'], incentives['penalty'], slash_validator['list'])

        func_call = self._contract.functions.slash(start_blocks, end_blocks, signer_indices, membership['history_index'], slash_validator[
                                                   'lessers'], slash_validator['greaters'], slash_validator['indices'], slash_group['lessers'], slash_group['greaters'], slash_group['indices'])

        return self.__wallet.send_transaction(func_call)

    def get_slashable_downtime_window(self, start_block: int, end_block: int = None) -> dict:
        """
        Calculate the slashable window with respect to a provided start or end block number

        Parameters:
            start_block: int
                First block of the downtime. Determined from endBlock if not provided
            end_block: int
                Last block of the downtime. Determined from startBlock or grandparent of latest block if not provided
        """
        length = self.slashable_downtime()
        return self.get_downtime_window(length, start_block, end_block)
    
    def get_downtime_window(self, length: int, start_block: int = None, end_block: int = None) -> dict:
        """
        Calculate the downtime window with respect to a length and a provided start or end block number

        Parameters:
            length: int
                Window length
            start_block: int
                First block of the Downtime window. Determined from endBlock if not provided
            end_block: int
                Last block of the Downtime window. Determined from startBlock or grandparent of latest block if not provided
        """
        if start_block and end_block:
            if end_block - start_block + 1 != length:
                raise Exception(f"Start and end block must define a window of {length} blocks")
            return { 'start': start_block, 'end': end_block, 'length': length }
        
        if end_block:
            return { 'start': end_block - length + 1, 'end': end_block, 'length': length }
        
        if start_block:
            return { 'start': start_block, 'end': start_block + length - 1, 'length': length }
        
        latest = self.web3.eth.blockNumber

        return { 'start': latest - length + 1, 'end': latest, 'length': length }
