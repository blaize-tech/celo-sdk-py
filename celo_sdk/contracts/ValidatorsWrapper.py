from typing import List

from celo_sdk.contracts.base_wrapper import BaseWrapper
from celo_sdk.registry import Registry

from web3 import Web3


class Validators(BaseWrapper):
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

    def set_next_commission_update(self, commission: int, parameters: dict = None) -> str:
        """
        Queues an update to a validator group's commission

        Parameters:
            commission: int
                Fixidity representation of the commission this group receives on epoch
                payments made to its members
        Returns:
            str
                Transaction hash
        """
        func_call = self._contract.functions.setNextCommissionUpdate(
            commission)

        return self.__wallet.send_transaction(func_call, parameters)

    def update_commission(self, parameters: dict = None) -> str:
        """
        Updates a validator group's commission based on the previously queued update

        Returns:
            str
                Transaction hash
        """
        func_call = self._contract.functions.updateCommission()

        return self.__wallet.send_transaction(func_call, parameters)

    def get_validator_locked_gold_requirements(self) -> dict:
        """
        Returns the Locked Gold requirements for validators

        Returns:
            dict
                The Locked Gold requirements for validators
        """
        res = self._contract.functions.getValidatorLockedGoldRequirements().call()

        return {'value': res[0], 'duration': res[1]}

    def get_group_locked_gold_requirements(self) -> dict:
        """
        Returns the Locked Gold requirements for validator groups

        Returns:
            dict
                The Locked Gold requirements for validator groups
        """
        res = self._contract.functions.getGroupLockedGoldRequirements().call()

        return {'value': res[0], 'duration': res[1]}

    def get_account_locked_gold_requirement(self, account: str) -> int:
        """
        Returns the Locked Gold requirements for specific account

        Returns:
            int
                The Locked Gold requirements for a specific account
        """
        return self._contract.functions.getAccountLockedGoldRequirement(account).call()

    def get_slashing_multiplier_reset_period(self) -> int:
        """
        Returns the reset period, in seconds, for slashing multiplier

        Returns:
            int
        """
        return self._contract.functions.slashingMultiplierResetPeriod().call()

    def get_commission_update_delay(self) -> int:
        """
        Returns the update delay, in blocks, for the group commission

        Returns:
            int
        """
        return self._contract.functions.commissionUpdateDelay().call()

    def get_config(self) -> dict:
        """
        Returns current configuration parameters

        Returns:
            dict
        """
        validator_locked_gold_requirements = self.get_validator_locked_gold_requirements()
        group_locked_gold_requirements = self.get_group_locked_gold_requirements()
        max_group_size = self._contract.functions.maxGroupSize().call()
        membership_history_length = self._contract.functions.membershipHistoryLength().call()
        slashing_multiplier_reset_period = self.get_slashing_multiplier_reset_period().call()
        commission_update_delay = self.get_commission_update_delay().call()

        return {
            'validator_locked_gold_requirements': validator_locked_gold_requirements,
            'group_locked_gold_requirements': group_locked_gold_requirements,
            'max_group_size': max_group_size,
            'membership_history_length': membership_history_length,
            'slashing_multiplier_reset_period': slashing_multiplier_reset_period,
            'commission_update_delay': commission_update_delay
        }

    def validator_signer_to_account(self, signer_address: str) -> str:
        """
        Returns the account associated with `signer`

        Parameters:
            signer_address: str
                The address of an account or currently authorized validator signer
        Returns:
            str
                The associated account
        """
        account_contract = self.create_and_get_contract_by_name('Accounts')

        return account_contract.validator_signer_to_account(signer_address)

    def signer_to_account(self, signer_address: str) -> str:
        """
        Returns the account associated with `signer`

        Parameters:
            signer_address: str
                The address of the account or previously authorized signer
        Returns:
            str
                The associated account
        """
        account_contract = self.create_and_get_contract_by_name('Accounts')

        return account_contract.signer_to_account(signer_address)

    def update_bls_public_key(self, bls_public_key: str, bls_pop: str) -> str:
        """
        Updates a validator's BLS key

        Parameters:
            bls_public_key: str
                The BLS public key that the validator is using for consensus, should pass proof
                of possession. 48 bytes
            bls_pop: str
                The BLS public key proof-of-possession, which consists of a signature on the
                account address. 96 bytes
        Returns:
            str
                True upon success
        """
        func_call = self._contract.functions.updateBlsPublicKey(
            bls_public_key, bls_pop)

        return self.__wallet.send_transaction(func_call)

    def is_validator(self, address: str) -> bool:
        """
        Returns whether a particular account has a registered validator

        Parameters:
            address: str
                The account
        Returns:
            bool
                Whether a particular address is a registered validator
        """
        return self._contract.functions.isValidator(address).call()

    def is_validator_group(self, address: str) -> bool:
        """
        Returns whether a particular account has a registered validator group

        Parameters:
            address: str
                The account
        Returns:
            bool
                Whether a particular address is a registered validator group
        """
        return self._contract.functions.isValidatorGroup(address).call()

    def meets_validator_balance_requirements(self, address: str) -> bool:
        """
        Returns whether an account meets the requirements to register a validator

        Parameters:
            address: str
                The account
        Returns:
            bool
                Whether an account meets the requirements to register a validator
        """
        locker_gold_contract = self.create_and_get_contract_by_name(
            'LockedGold')
        total = locker_gold_contract.get_account_total_locked_gold(address)
        reqs = self.get_validator_locked_gold_requirements()

        return reqs['value'] <= total

    def meets_validator_group_balance_requirements(self, address: str) -> bool:
        """
        Returns whether an account meets the requirements to register a group

        Parameters:
            address: str
                The account
        Returns:
            bool
                Whether an account meets the requirements to register a group
        """
        locker_gold_contract = self.create_and_get_contract_by_name(
            'LockedGold')
        total = locker_gold_contract.get_account_total_locked_gold(address)
        reqs = self.get_group_locked_gold_requirements()

        return reqs['value'] <= total

    def get_validator(self, address: str, block_number: int = None) -> dict:
        """
        Get validator information

        Parameters:
            address: str
            block_number: int
        Returns:
            dict
                Validator information
        """
        if block_number != None:
            res = self._contract.functions.getValidator(
                address).call(block_identifier=block_number)
        else:
            res = self._contract.functions.getValidator(address).call()

        accounts_contract = self.create_and_get_contract_by_name('Accounts')
        name = accounts_contract.get_name(address)

        return {
            'name': name,
            'address': address,
            'ecdsa_public_key': res[0],
            'bls_public_key': res[1],
            'affiliation': res[2],
            'score': res[3],
            'signer': res[4]
        }

    def get_validator_from_signer(self, address: str, block_number: int = None) -> dict:
        """
        Parameters:
            address: str
            block_number: int
        Returns:
            dict
        """
        account = self.signer_to_account(address)
        if account == self.null_address or not self.is_validator(account):
            return {
                'name': 'Unregistered validator',
                'address': address,
                'ecdsa_public_key': '',
                'bls_public_key': '',
                'affiliation': '',
                'score': 0,
                'signer': address
            }
        else:
            return self.get_validator(account, block_number=block_number)

    def get_validator_group(self, address: str, get_affiliates: bool = True, block_number: int = None) -> dict:
        """
        Get ValidatorGroup information

        Parameters:
            address: str
            get_affiliates: bool
            block_number: int
        Returns:
            dict
        """
        if block_number != None:
            res = self._contract.functions.getValidatorGroup(
                address).call(block_identifier=block_number)
        else:
            res = self._contract.functions.getValidatorGroup(address).call()

        accounts_contract = self.create_and_get_contract_by_name('Accounts')
        name = accounts_contract.get_name(address, block_number=block_number)

        affiliates = []
        if get_affiliates:
            validators = self.get_registered_validators(
                block_number=block_number)
            affiliates = [el for el in validators if el['affiliation']
                          and el['affiliation'] == address and el['address'] not in res[0]]
        return {
            'name': name,
            'address': address,
            'members': res[0],
            'commission': res[1],
            'next_commission': res[2],
            'next_commission_block': res[3],
            'members_updated': max(res[4]),
            'affiliates': [el['address'] for el in affiliates],
            'slashing_multiplier': res[5],
            'last_slashed': res[6]
        }

    def get_validator_membership_history(self, validator: str) -> List[dict]:
        """
        Returns the Validator's group membership history

        Parameters:
            validator: str
                The validator whose membership history to return
        Returns:
            List[dict]
        """
        res = self._contract.functions.getMembershipHistory(validator).call()

        length = min(len(res[0]), len(res[1]))

        result = []
        for ind in range(length):
            result.append({'epoch': res[0][ind], 'group': res[1][ind]})

        return result

    def get_validator_membership_history_extra_data(self, validator: str) -> dict:
        """
        Returns extra data from the Validator's group membership history

        Parameters:
            validator: str
                The validator whose membership history to return
        Returns:
            dict
                The group membership history of a validator
        """
        res = self._contract.functions.getMembershipHistory(validator).call()

        return {'last_removed_from_group_timestamp': res[2], 'tail': res[3]}

    def get_validator_group_size(self, group: str) -> int:
        """
        Get the size (amount of members) of a ValidatorGroup

        Parameters:
            group: str
        Returns:
            int
        """
        return self._contract.functions.getGroupNumMembers(group).call()

    def get_registered_validators_addresses(self, block_number: int = None) -> List[str]:
        """
        Get list of registered validator addresses

        Parameters:
            block_number: int
        Returns:
            List[str]
        """
        if block_number != None:
            return self._contract.functions.getRegisteredValidators().call(block_identifier=block_number)
        else:
            return self._contract.functions.getRegisteredValidators().call()

    def get_registered_validator_groups_addresses(self) -> List[str]:
        """
        Get list of registered validator group addresses

        Returns:
            List[str]
        """
        return self._contract.functions.getRegisteredValidatorGroups().call()

    def get_registered_validators(self, block_number: int = None) -> List[dict]:
        """
        Get list of registered validators
        """
        vg_addresses = self.get_registered_validators_addresses(
            block_number=block_number)

        res = []
        for address in vg_addresses:
            res.append(self.get_validator(address, block_number=block_number))

        return res

    def get_registered_validator_groups(self) -> List[dict]:
        """
        Get list of registered validator groups
        """
        vg_address = self.get_registered_validator_groups_addresses()

        res = []
        for address in vg_address:
            res.append(self.get_validator_group(address, get_affiliates=False))

        return res

    def get_epoch_number(self) -> int:
        return self._contract.functions.getEpochNumber().call()

    def get_epoch_size(self) -> int:
        return self._contract.functions.getEpochSize().call()

    def register_validator(self, ecdsa_public_key: str, bls_public_key: str, bls_pop: str) -> str:
        """
        Registers a validator unaffiliated with any validator group

        Parameters:
            ecdsa_public_key: str
            bls_public_key: str
            bls_pop: str
        Returns:
            str
                Transaction hash
        """
        func_call = self._contract.functions.registerValidator(
            ecdsa_public_key, bls_public_key, bls_pop)

        return self.__wallet.send_transaction(func_call)

    def deregister_validator(self, validator_address: str) -> str:
        """
        De-registers a validator, removing it from the group for which it is a member

        Parameters:
            validator_address: str
                Address of the validator to deregister
        Returns:
            str
                Transaction hash
        """
        try:
            all_validators = self.get_registered_validators_addresses()
            idx = all_validators.index(validator_address)
            func_call = self._contract.functions.deregisterValidator(idx)

            return self.__wallet.send_transaction(func_call)
        except ValueError:
            raise Exception(
                f"{validator_address} is not a registered validator")

    def register_validator_group(self, commission: int, parameters: dict = None) -> str:
        """
        Registers a validator group with no member validators
        Fails if the account is already a validator or validator group
        Fails if the account does not have sufficient weight

        Parameters:
            commission: int
                The commission this group receives on epoch payments made to its members
        Returns:
            str
                Transaction hash
        """
        func_call = self._contract.functions.registerValidatorGroup(commission)

        return self.__wallet.send_transaction(func_call, parameters)

    def deregister_validator_group(self, validator_group_address: str) -> str:
        """
        De-registers a validator Group

        Parameters:
            validator_group_address: str
                Address of the validator group to deregister
        Returns:
            str
                Transaction hash
        """
        try:
            all_groups = self.get_registered_validator_groups_addresses()
            idx = all_groups.index(validator_group_address)
            func_call = self._contract.functions.deregisterValidatorGroup(idx)

            return self.__wallet.send_transaction(func_call)
        except ValueError:
            raise Exception(
                f"{validator_group_address} is not a registered validator")

    def affiliate(self, group: str, parameters: dict = None) -> str:
        """
        Affiliates a validator with a group, allowing it to be added as a member
        De-affiliates with the previously affiliated group if present

        Parameters:
            group: str
                The validator group with which to affiliate
        Returns:
            str
                Transaction hash
        """
        func_call = self._contract.functions.affiliate(group)

        return self.__wallet.send_transaction(func_call, parameters)

    def deaffiliate(self) -> str:
        func_call = self._contract.functions.deaffiliate()

        return self.__wallet.send_transaction(func_call)

    def force_deaffiliate_if_validator(self, validator_account: str) -> str:
        """
        Removes a validator from the group for which it is a member

        Parameters:
            validator_account: str
        Returns:
            str
                Transaction hash
        """
        func_call = self._contract.functions.forceDeaffiliateIfValidator(
            validator_account)

        return self.__wallet.send_transaction(func_call)

    def reset_slashing_multiplier(self) -> str:
        """
        Resets a group's slashing multiplier if it has been >= the reset period since
        the last time the group was slashed

        Returns:
            str
                Transaction hash
        """
        func_call = self._contract.functions.resetSlashingMultiplier()

        return self.__wallet.send_transaction(func_call)

    def add_member(self, group: str, validator: str, parameters: dict = None) -> str:
        """
        Adds a member to the end of a validator group's list of members
        Fails if `validator` has not set their affiliation to this account

        Parameters:
            group: str
            validator: str
                The validator to add to the group
        Returns:
            str
                Transaction hash
        """
        num_member = self.get_validator_group_size(group)
        if num_member == 0:
            election_contract = self.create_and_get_contract_by_name(
                'Election')
            vote_weight = election_contract.get_total_votes_for_group(group)
            lesser_greater = election_contract.find_lesser_and_greater_after_vote(
                group, vote_weight)
            func_call = self._contract.functions.addFirstMember(
                validator, lesser_greater['lesser'], lesser_greater['greater'])

            return self.__wallet.send_transaction(func_call, parameters)
        else:
            func_call = self._contract.functions.addMember(validator)

            return self.__wallet.send_transaction(func_call, parameters)

    def remove_member(self, validator: str) -> str:
        """
        Removes a member from a ValidatorGroup
        The ValidatorGroup is specified by the `from` of the tx

        Parameters:
            validator: str
                The Validator to remove from the group
        Returns:
            str
                Transaction hash
        """
        func_call = self._contract.functions.removeMember(validator)

        return self.__wallet.send_transaction(func_call)

    def reorder_member(self, group_addr: str, validator: str, new_index: int, parameters: dict = None) -> str:
        """
        Reorders a member within a validator group
        Fails if `validator` is not a member of the account's validator group

        Parameters:
            group_addr: str
                The validator group
            validator: str
                The validator to reorder
            new_index: int
                New position for the validator
        Returns:
            str
                Transaction hash
        """
        try:
            group = self.get_validator_group(group_addr)

            if new_index < 0 or new_index >= len(group['members']):
                raise Exception(
                    f"Invalid index {new_index}; max index is {len(group['members']) - 1}")

            current_idx = group['members'].index(validator)

            if current_idx == new_index:
                raise Exception(
                    f"Validator is already in position {new_index}")

            del group['members'][current_idx]
            group['members'].insert(new_index, validator)

            next_member = self.null_address if len(
                group['members']) - 1 == new_index else group['members'][new_index + 1]
            prev_member = self.null_address if new_index == 0 else group['members'][new_index - 1]

            func_call = self._contract.functions.reorderMember(
                validator, next_member, prev_member)

            return self.__wallet.send_transaction(func_call, parameters)
        except ValueError:
            raise Exception(
                f"ValidatorGroup {group_addr} does not include ${validator}")

    def get_validator_rewards(self, epoch_number: int) -> List[dict]:
        """
        Retrieves ValidatorRewards for epochNumber

        Parameters:
            epoch_number: int
                The epoch to retrieve ValidatorRewards at
        Returns:
            List[dict]
        """
        block_number = self.get_last_block_number_for_epoch(epoch_number)
        events = self._contract.events.ValidatorEpochPaymentDistributed.getLogs(
            fromBlock=block_number, toBlock=block_number)

        validator = []
        for event in events:
            validator.append(self.get_validator(event['args']['validator']))

        validator_group = []
        for event in events:
            validator_group.append(self.get_validator_group(
                event['args']['group'], False))

        res = []
        for ind, el in enumerate(events):
            res.append({
                'epoch_number': epoch_number,
                'validator': validator[ind],
                'validator_payment': el['args']['validatorPayment'],
                'group': validator_group[ind],
                'group_payment': el['args']['groupPayment']
            })

        return res

    def current_signer_set(self) -> List[str]:
        """
        Returns the current set of validator signer addresses

        Returns:
            List[str]
        """
        n = self._contract.functions.numberValidatorsInCurrentSet().call()

        res = []
        for idx in range(n):
            res.append(
                self._contract.functions.validatorSignerAddressFromCurrentSet(idx).call())

        return res

    def current_validator_account_set(self) -> List[dict]:
        """
        Returns the current set of validator signer and account addresses

        Returns:
            List[dict]
        """
        signer_address = self.current_signer_set()

        account_addresses = []
        for address in signer_address:
            account_addresses.append(self.validator_signer_to_account(address))

        res = []
        for signer, account in zip(signer_address, account_addresses):
            res.append({'signer': signer, 'account': account})

        return res

    def get_validator_membership_history_index(self, validator: dict, block_number: int = None) -> dict:
        """
        Returns the group membership for `validator`

        Parameters:
            validator: dict,
                Address of validator to retrieve group membership for
            block_number: int
                Block number to retrieve group membership at
        Returns:
            dict
                Group and membership history index for `validator`
        """
        block_number = block_number if block_number else self.web3.eth.blockNumber
        block_epoch = self.get_epoch_number_of_block(block_number)
        account = self.validator_signer_to_account(validator['signer'])
        membership_history = self.get_validator_membership_history(account)
        history_index = self.find_validator_membership_history_index(
            block_epoch, membership_history)
        group = membership_history[history_index]['group']

        return {'group': group, 'history_index': history_index}

    def find_validator_membership_history_index(self, epoch: int, history: List[dict]) -> int:
        """
        Returns the index into `history` for `epoch`

        Parameters:
            epoch: int
                The needle
            history: List[dict]
                The haystack
        Returns:
            int
                Index for epoch or -1
        """
        rev_history = reversed(history)
        rev_index = None
        for ind, el in enumerate(rev_history):
            if el['epoch'] <= epoch:
                rev_index = ind
                break

        return -1 if rev_index == None else len(history) - rev_index - 1

    def get_epoch_number_of_block(self, block: int) -> int:
        epoch_size = self.get_epoch_size()
        epoch_number = int(block / epoch_size)
        if block % epoch_size == 0:
            return epoch_number
        else:
            epoch_number + 1

    def get_first_block_number_for_epoch(self, epoch_number: int) -> int:
        if epoch_number == 0:
            return 0
        epoch_size = self.get_epoch_size()
        return (epoch_number - 1) * epoch_size + 1

    def get_last_block_number_for_epoch(self, epoch_number: int) -> int:
        if epoch_number == 0:
            return 0
        epoch_size = self.get_epoch_size()
        first_block = self.get_first_block_number_for_epoch(epoch_number)
        return first_block + (epoch_size - 1)
