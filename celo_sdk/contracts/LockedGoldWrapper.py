import time
from typing import List

from web3 import Web3

from celo_sdk.contracts.base_wrapper import BaseWrapper
from celo_sdk.registry import Registry
from celo_sdk.utils import utils


class LockedGold(BaseWrapper):
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

    def withdraw(self, index: int) -> str:
        """
        Withdraws a gold that has been unlocked after the unlocking period has passed

        Parameters:
            index: int
                The index of the pending withdrawal to withdraw
        Returns:
            str
                Transaction hash
        """
        func_call = self._contract.functions.withdraw(index)

        return self.__wallet.send_transaction(func_call)

    def lock(self, parameters: dict = None) -> str:
        """
        Locks gold to be used for voting

        Parameters:
            value: int
                Value of gold to be locked

        Returns:
            str
                Transaction hash
        """
        func_call = self._contract.functions.lock()

        return self.__wallet.send_transaction(func_call, parameters=parameters)

    def unlock(self, value: int) -> str:
        """
        Unlocks gold that becomes withdrawable after the unlocking period

        Parameters:
            value: int
                The amount of gold to unlock

        Returns:
            str
                Transaction hash
        """
        func_call = self._contract.functions.unlock(value)

        return self.__wallet.send_transaction(func_call)

    def get_pending_withdrawals_total_value(self, account: str) -> float:
        pending_withdrawals = self.get_pending_withdrawals(account)
        values = [el['value'] for el in pending_withdrawals]

        return sum(values)

    def relock(self, account: str, value: int) -> List[str]:
        """
        Relocks gold that has been unlocked but not withdrawn

        Parameters:
            account: str
            value: int
                The value to relock from pending withdrawals
        """
        pending_withdrawals = self.get_pending_withdrawals(account)
        # Ensure there are enough pending withdrawals to relock
        total_value = self.get_pending_withdrawals_total_value(account)

        if total_value < value:
            raise Exception(
                f"Not enough pending withdrawals to relock {value}")

        for ind, withd in enumerate(pending_withdrawals):
            if ind != 0:
                if not withd['time'] >= pending_withdrawals[ind - 1]['time']:
                    raise Exception(
                        "Pending withdrawals not sorted by timestamp")

        res = []
        remaining_to_relock = value
        for ind in reversed(range(len(pending_withdrawals))):
            value_to_relock = min(pending_withdrawals[ind]['value'], remaining_to_relock)
            if value_to_relock > 0:
                remaining_to_relock -= value_to_relock
                res.append(self.relock_single(ind, value_to_relock))

        return res

    def relock_single(self, index: int, value: int) -> str:
        """
        Relocks gold that has been unlocked but not withdrawn

        Parameters:
            index: int
                The index of the pending withdrawal to relock from
            value: int
                The value to relock from the specified pending withdrawal
        Returns:
            str
                Transaction hash
        """
        func_call = self._contract.functions.relock(index, value)

        return self.__wallet.send_transaction(func_call)

    def get_account_total_locked_gold(self, account: str) -> int:
        """
        Returns the total amount of locked gold for an account

        Parameters:
            account: str
                The account
        Returns:
            int
                The total amount of locked gold for an account
        """
        return self._contract.functions.getAccountTotalLockedGold(account).call()

    def get_total_locked_gold(self) -> int:
        """
        Returns the total amount of locked gold in the system. Note that this does not include
        gold that has been unlocked but not yet withdrawn

        Returns:
            int
                The total amount of locked gold in the system
        """
        return self._contract.functions.getTotalLockedGold().call()

    def get_account_nonvoting_locked_gold(self, account: str) -> int:
        """
        Returns the total amount of non-voting locked gold for an account

        Parameters:
            account: str
                The account
        Returns:
            int
                The total amount of non-voting locked gold for an account
        """
        return self._contract.functions.getAccountNonvotingLockedGold(account).call()

    def get_config(self) -> dict:
        """
        Returns current configuration parameters
        """
        unlocking_period = self._contract.functions.unlockingPeriod().call()
        total_locked_gold = self.get_total_locked_gold()

        return {'unlocking_period': unlocking_period, 'total_locked_gold': total_locked_gold}

    def get_account_summary(self, account: str) -> dict:
        non_voting = self.get_account_nonvoting_locked_gold(account)
        total = self.get_account_total_locked_gold(account)
        validators_contract = self.create_and_get_contract_by_name(
            'Validators')
        requiremet = validators_contract.get_account_locked_gold_requirement(
            account)
        pending_withdrawals = self.get_pending_withdrawals(account)

        return {
            'locked_gold': {
                'total': total,
                'non_voting': non_voting,
                'requirement': requiremet
            },
            'pending_withdrawals': pending_withdrawals
        }

    def get_accounts_slashed(self, epoch_number: int) -> List[dict]:
        """
        Retrieves AccountSlashed for epochNumber

        Parameters:
            epoch_number: int
                The epoch to retrieve AccountSlashed at
        """
        validators_contract = self.create_and_get_contract_by_name(
            'Validators')
        from_block = validators_contract.get_first_block_number_for_epoch(
            epoch_number)
        to_block = validators_contract.get_last_block_number_for_epoch(
            epoch_number)
        events = self._contract.events.AccountSlashed.getLogs(
            fromBlock=from_block, toBlock=to_block)

        res = []
        for event in events:
            res.append({'epoch_number': epoch_number, 'slashed': event['args']['slashed'], 'penalty': event[
                       'args']['penalty'], 'reporter': event['args']['reporter'], 'reward': event['args']['reward']})
        
        return res

    def compute_initial_parameters_for_slashing(self, account: str, penalty: int) -> dict:
        """
        Computes parameters for slashing `penalty` from `account`

        Parameters:
            account: str
                The account to slash
            penalty: int
                The amount to slash as penalty
        Returns:
            Dict of (group, voting gold) to decrement from `account`
        """
        election_contract = self.create_and_get_contract_by_name('Election')
        eligible = election_contract.get_eligible_validator_groups_votes()
        groups = [{'address': el['address'], 'value': el['votes']} for el in eligible]
        return self.compute_parameters_for_slashing(account, penalty, groups)
    
    def compute_parameters_for_slashing(self, account: str, penalty: int, groups: List[dict]) -> dict:
        changed = self.compute_decrements_for_slashing(account, penalty, groups)
        changes = utils.linked_list_changes(groups, changed)
        indices = [el['index'] for el in changed]
        changes['indices'] = indices

        return changes

    def compute_decrements_for_slashing(self, account: str, penalty: int, all_groups: List[dict]) -> List[dict]:
        """
        Returns how much voting gold will be decremented from the groups voted by an account
        """
        non_voting = self.get_account_nonvoting_locked_gold(account)
        if penalty < non_voting:
            return []
        
        difference = penalty - non_voting

        election_contract = self.create_and_get_contract_by_name('Election')
        groups = election_contract.get_groups_voted_for_by_account(account)
        res = []

        for ind, group in enumerate(groups):
            total_votes = None
            for el in all_groups:
                if el['address'] == group:
                    total_votes = el['value']
            if total_votes == None:
                raise Exception(f"Cannot find group {group}")
            votes = election_contract.get_total_votes_for_group_by_account(group, account)
            slashed_votes = votes if votes < difference else difference

            res.append({'address': group, 'value': total_votes - slashed_votes, 'index': ind})

            difference -= slashed_votes

            if difference == 0:
                break
        
        return res

    def get_pending_withdrawals(self, account: str) -> List[dict]:
        """
        Returns the pending withdrawals from unlocked gold for an account

        Parameters:
            account: str
                The address of the account
        Returns:
            The value and timestamp for each pending withdrawal
        """
        withdrawals = self._contract.functions.getPendingWithdrawals(
            account).call()

        res = []
        for a, b in zip(withdrawals[1], withdrawals[0]):
            res.append({'time': a, 'value': b})

        return res
