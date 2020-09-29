import sys

from celo_sdk.contracts.base_wrapper import BaseWrapper
from celo_sdk.registry import Registry

from web3 import Web3


class Election(BaseWrapper):
    """
    Contract for voting for validators and managing validator groups

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

    def electable_validators(self) -> dict:
        """
        Returns the minimum and maximum number of validators that can be elected
        """
        min_max = self._contract.functions.electableValidators().call()
        return { 'min': min_max[0], 'max': min_max[1]}
    
    def electability_threshold(self) -> int:
        """
        Returns the current election threshold
        """
        return self._contract.functions.getElectabilityThreshold().call()

    def validator_signer_address_from_set(self, index: int, block_number: int) -> str:
        """
        Gets a validator address from the validator set at the given block number

        Parameters:
            index: int
                Index of requested validator in the validator set
            block_number: int
                Block number to retrieve the validator set from
        Returns:
            Address of validator at the requested index
        """
        return self._contract.functions.validatorSignerAddressFromSet(index, block_number).call()
    
    def validator_signer_address_from_current_set(self, index: int) -> str:
        """
        Gets a validator address from the current validator set
        
        Parameters:
            index: int
                Index of requested validator in the validator set
        Returns:
            Address of validator at the requested index
        """
        return self._contract.functions.validatorSignerAddressFromCurrentSet(index).call()
    
    def number_validators_in_set(self, block_number: int) -> int:
        """
        Gets the size of the validator set that must sign the given block number

        Parameters:
            block_number: int
                Block number to retrieve the validator set from
        Returns:
            Size of the validator set
        """
        return self._contract.functions.numberValidatorsInSet(block_number).call()
    
    def number_validators_in_current_set(self) -> int:
        """
        Gets the size of the current elected validator set

        Returns:
            Size of the current elected validator set
        """
        return self._contract.functions.numberValidatorsInCurrentSet().call()
    
    def get_total_votes(self) -> int:
        """
        Returns the total votes received across all groups

        Returns:
            The total votes received across all groups
        """
        return self._contract.functions.getTotalVotes().call()
    
    def get_current_validator_signers(self) -> list:
        """
        Returns the current validator signers using the precompiles

        Returns:
            List of current validator signers
        """
        return self._contract.functions.getCurrentValidatorSigners().call()
    
    def get_validator_signers(self, block_number: int) -> list:
        """
        Returns the validator signers for block `blockNumber`

        Parameters:
            block_number: int
                Block number to retrieve signers for
        Returns:
            Address of each signer in the validator set
        """
        num_validators = self.number_validators_in_set(block_number)

        results = []
        for ind in range(num_validators):
            results.append(self.validator_signer_address_from_set(ind, block_number))
        
        return results
    
    def elect_validator_signers(self, min: int = None, max: int = None) -> list:
        """
        Returns a list of elected validators with seats allocated to groups via the D'Hondt method

        Parameters:
            min: int
            max: int
        Returns:
            The list of elected validators
        """
        if not min or not max:
            config = self.get_config()
            min_arg = min if min else config['min']
            max_arg = max if max else config['max']
            return self._contract.functions.electNValidatorSigners(min_arg, max_arg).call()
        else:
            return self._contract.functions.electValidatorSigners().call()
    
    def get_total_votes_for_group(self, group: str, block_number: int = None) -> int:
        """
        Returns the total votes for `group`

        Parameters:
            goup: str
                The address of the validator group
            block_number: int
        Returns:
            The total votes for `group`
        """
        if block_number:
            votes = self._contract.functions.getTotalVotesForGroup(group).call(block_identifier=block_number)
        else:
            votes = self._contract.functions.getTotalVotesForGroup(group).call()
        
        return votes
    
    def get_total_votes_for_group_by_account(self, group: str, account: str) -> int:
        """
        Returns the total votes for `group` made by `account`

        Parameters:
            group: str
                The address of the validator group
            account: str
                The address of the voting account
        Returns:
            The total votes for `group` made by `account`
        """
        return self._contract.functions.getTotalVotesForGroupByAccount(group, account).call()

    def get_active_votes_for_group(self, group: str, block_number: int = None) -> int:
        """
        Returns the active votes for `group`

        Parameters:
            group: str
                The address of the validator group
            block_number: int
        Returns:
            The active votes for `group`
        """
        if block_number:
            votes = self._contract.functions.getActiveVotesForGroup(group).call(block_identifier=block_number)
        else:
            votes = self._contract.functions.getActiveVotesForGroup(group).call()
        
        return votes
    
    def get_groups_voted_for_by_account(self, account: str) -> list:
        """
        Returns the groups that `account` has voted for

        Parameters:
            account: str
                The address of the account casting votes
        Returns:
            The groups that `account` has voted for
        """
        return self._contract.functions.getGroupsVotedForByAccount().call()
    
    def get_votes_for_group_by_account(self, account: str, group: str, block_number: int = None) -> dict:
        """
        Returns votes for group by specific account

        Parameters:
            account: str
            group: str
            block_number: int
        """
        if block_number:
            pending = self._contract.functions.getPendingVotesForGroupByAccount(group, account).call(block_identifier=block_number)
            active = self._contract.functions.getActiveVotesForGroupByAccount(group, account).call(block_identifier=block_number)
        else:
            pending = self._contract.functions.getPendingVotesForGroupByAccount(group, account).call()
            active = self._contract.functions.getActiveVotesForGroupByAccount(group, account).call()
        
        return { 'group': group, 'pending': pending, 'active': active }
    
    def get_voter(self, account: str, block_number: int = None) -> dict:
        """
        Parameters:
            account: str
            block_number: int
        """
        if block_number:
            groups = self._contract.functions.getGroupsVotedForByAccount(account).call(block_identifier=block_number)
        else:
            groups = self._contract.functions.getGroupsVotedForByAccount(account).call()
        
        votes = []
        for el in groups:
            votes.append(self.get_votes_for_group_by_account(account, el, block_number=block_number))
        
        return { 'address': account, 'votes': votes }
    
    def hash_pending_votes(self, account: str) -> bool:
        """
        Returns whether or not the account has any pending votes

        Parameters:
            account: str
                The address of the account casting votes
        """
        groups = self._contract.functions.getGroupsVotedForByAccount(account).call()
        is_pending = []
        for g in groups:
            is_pending.append(self._contract.functions.getPendingVotesForGroupByAccount(g,account).call() > 0)
        
        return True in is_pending
    
    def has_activatable_pending_votes(self, account: str) -> bool:
        groups = self._contract.functions.getGroupsVotedForByAccount(account).call()
        is_activatable = []
        for g in groups:
            is_activatable.append(self._contract.functions.hasActivatablePendingVotes(account, g).call())
        
        return True in is_activatable
    
    def get_config(self) -> dict:
        """
        Returns current configuration parameters
        """
        electability_threshold = self.electability_threshold()
        total_votes = self.get_total_votes()

        return {
            'electable_validators': self.electable_validators(),
            'electability_threshold': electability_threshold,
            'max_num_groups_voted_for': self._contract.functions.maxNumGroupsVotedFor().call(),
            'total_votes': total_votes,
            'current_threshold': total_votes * electability_threshold
        }
    
    def get_validator_group_votes(self, address: str) -> dict:
        votes = self._contract.functions.getTotalVotesForGroup(address).call()
        eligible = self._contract.functions.getGroupEligibility(address).call()
        num_votes_receivable = self._contract.functions.getNumVotesReceivable(address).call()
        accounts_contract = self.create_and_get_contract_by_name('Accounts')
        name = accounts_contract.get_name(address)

        return {
            'address': address,
            'name': name,
            'votes': votes,
            'capacity': num_votes_receivable - votes,
            'eligible': eligible
        }
    
    def get_validator_groups_votes(self) -> list:
        """
        Returns the current registered validator groups and their total votes and eligibility
        """
        validators_contract = self.create_and_get_contract_by_name('Validators')
        groups = validators_contract.get_registered_validator_groups_addresses()
        result = []
        for g in groups:
            result.append(self.get_validator_group_votes(g))
        
        return result
    
    def _activate(self, group: str) -> str:
        func_call = self._contract.functions.activate(group)
        return self.__wallet.send_transaction(func_call)

    def activate(self, account: str) -> list:
        """
        Activates any activatable pending votes

        Parameters:
            account: str
                The account with pending votes to activate
        """
        groups = self._contract.functions.getGroupsVotedForByAccount(account).call()

        is_activatable = []
        for g in groups:
            is_activatable.append(self._contract.functions.hasActivatablePendingVotes(account, g).call())

        groups_activatable = []
        for (addrs, is_actv) in zip(groups, is_activatable):
            if is_actv:
                groups_activatable.append(addrs)
        
        activates = [self._activate(g) for g in groups_activatable]

        return activates

    def revoke_pending(self, account: str, group: str, value: int) -> str:
        """
        Parameters:
            account: str
            group: str
            value: int
        Returns:
            Transaction hash
        """
        groups = self._contract.functions.getGroupsVotedForByAccount(account).call()
        index = groups.index(group)
        lesser_greater = self.find_lesser_and_greater_after_vote(group, value * -1)
        
        func_call = self._contract.functions.revokePending(group, value, lesser_greater['lesser'], lesser_greater['greater'], index)
        return self.__wallet.send_transaction(func_call)

    def revoke_active(self, account: str, group: str, value: int) -> str:
        """
        Parameters:
            account: str
            group: str
            value: int
        Returns:
            Transaction hash
        """
        groups = self._contract.functions.getGroupsVotedForByAccount(account).call()
        index = groups.index(group)
        lesser_greater = self.find_lesser_and_greater_after_vote(group, value * -1)
        
        func_call = self._contract.functions.revokeActive(group, value, lesser_greater['lesser'], lesser_greater['greater'], index)
        return self.__wallet.send_transaction(func_call)
    
    def revoke(self, account: str, group: str, value: int) -> list:
        """
        Parameters:
            account: str
            group: str
            value: int
        Returns:
            list
        """
        vote = self.get_votes_for_group_by_account(account, group)
        if value > vote['pending'] + vote['active']:
            raise Exception(f"Can't revoke more votes for {group} than have been made by {account}")
        
        txos = []
        pending_value = min(vote['pending'], value)
        if pending_value > 0:
            txos.append(self.revoke_pending(account, group, pending_value))
        if pending_value < value:
            active_value = value - pending_value
            txos.append(self.revoke_active(account, group, active_value))
        
        return txos
    
    def vote(self, validator_group: str, value: int) -> str:
        """
        Increments the number of total and pending votes for `group`

        Parameters:
            validator_group: str
                The validator group to vote for
            value: int
                The amount of gold to use to vote
        Returns:
            Transaction hash
        """
        lesser_greater = self.find_lesser_and_greater_after_vote(validator_group, value)
        func_call = self._contract.functions.vote(validator_group, value, lesser_greater['lesser'], lesser_greater['greater'])

        return self.__wallet.send_transaction(func_call)
    
    def get_eligible_validator_groups_votes(self) -> list:
        """
        Returns the current eligible validator groups and their total votes
        """
        res = self._contract.functions.getTotalVotesForEligibleValidatorGroups().call()
        length = min(len(res[0], res[1]))
        result = []
        
        for ind in range(length):
            result.append({ 
                'address': res[0][ind],
                'name': '',
                'votes': res[1][ind],
                'capacity': 0,
                'eligible': True
             })
        
        return result
    
    def find_lesser_and_greater_after_vote(self, voted_group: str, vote_weight: int) -> dict:
        current_votes = self.get_eligible_validator_groups_votes()
        selected_group = None
        for vote in current_votes:
            if vote['address'] == voted_group:
                selected_group = vote
                break
        vote_total = vote_weight if not selected_group else selected_group['votes'] + vote_weight

        greater_key = self.null_address
        lesser_key = self.null_address

        for vote in current_votes:
            if vote['address'] != voted_group:
                if vote['votes'] <= vote_total:
                    lesser_key = vote['address']
                    break
                greater_key = vote['address']
        
        return { 'lesser': lesser_key, 'greater': greater_key }
    
    def get_elected_validators(self, epoch_number: int) -> list:
        """
        Retrieves the set of validatorsparticipating in BFT at epochNumber

        Parameters:
            epoch_number: int
                The epoch to retrieve the elected validator set at
        """
        validators_contract = self.create_and_get_contract_by_name('Validators')

        block_number = validators_contract.get_first_block_number_for_epoch(epoch_number)
        signers = self.get_validator_signers(block_number)
        result = []

        for s in signers:
            result.append(validators_contract.get_validator_from_signer(s))
        
        return result
    
    def get_group_voter_rewards(self, epoch_number: int) -> list:
        """
        Retrieves GroupVoterRewards at epochNumber

        Parameters:
            epoch_number: int
                The epoch to retrieve GroupVoterRewards at
        """
        validators_contract = self.create_and_get_contract_by_name('Validators')

        block_number = validators_contract.get_last_block_number_for_epoch(epoch_number)
        events = self._contract.events.EpochRewardsDistributedToVoters.getLogs(fromBlock=block_number, toBlock=block_number)
        if not events:
            raise Exception("There are no events found for this epoch number")
        
        validators_contract = self.create_and_get_contract_by_name('Validators')
        
        validator_group = []
        for event in events:
            validator_group.append(validators_contract.get_validator_group(event['args']['group'], False))
        
        result = []
        for ind, event in enumerate(events):
            result.append({ 'epoch_number': epoch_number, 'group': validator_group[ind], 'group_voter_payment': event['args']['value'] })
        
        return result

    def get_voter_rewards(self, address: str, epoch_number: int, voter_share: dict = None) -> dict:
        """
        Retrieves VoterRewards for address at epochNumber

        Parameters:
            address: str
                The address to retrieve VoterRewards for
            epoch_number: int
                The epoch to retrieve VoterRewards at
            voter_share: dict
                Optionally address' share of group rewards
        """
        validators_contract = self.create_and_get_contract_by_name('Validators')

        active_vote_share = voter_share if voter_share else self.get_voter_share(address, validators_contract.get_last_block_number_for_epoch(epoch_number))

        group_voter_rewards = self.get_group_voter_rewards(epoch_number)

        voter_rewards = []
        for g in group_voter_rewards:
            if g['group'].lstrip('0x').lower() in active_vote_share:
                voter_rewards.append(g)
        
        result = []
        for v_r in voter_rewards:
            group = v_r['group']['address'].lstrip('0x').lower()
            result.append({
                'address': address,
                'address_payment': v_r['group_voter_payment'] * active_vote_share[group],
                'group': v_r['group'],
                'epoch_number': v_r['epoch_number']
            })
        
        return result

    def get_voter_share(self, address: str, block_number: int = None) -> dict:
        """
        Retrieves a voter's share of active votes

        Parameters:
            address: str
                The voter to retrieve share for
            block_number: int
                The block to retrieve the voter's share at
        """
        active_voter_votes = {}
        voter = self.get_voter(address, block_number)
        for vote in voter['votes']:
            group = vote['group'].lstrip('0x').lower()
            active_voter_votes[group] = vote['active']

        for addrs, number in active_voter_votes.items():
            active_voter_votes[addrs] = number / self.get_active_votes_for_group(address, block_number)
        
        return active_voter_votes
