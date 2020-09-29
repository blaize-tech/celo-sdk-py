import time
from typing import List

from web3 import Web3

from celo_sdk.contracts.base_wrapper import BaseWrapper
from celo_sdk.registry import Registry


class Governance(BaseWrapper):
    """
    Contract managing voting for governance proposals

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

        self.proposal_stage = ['None', 'Queued', 'Approval',
                               'Referendum', 'Execution', 'Expiration']
        self.vote_value = {'none': 'NONE',
                           'abstain': 'Abstain', 'no': 'No', 'yes': 'Yes'}

    def concurrent_proposals(self) -> int:
        """
        Querying number of possible concurrent proposals

        Returns:
            int
                Current number of possible concurrent proposals
        """
        return self._contract.functions.concurrentProposals().call()

    def last_dequeue(self) -> int:
        """
        Query proposal dequeue frequency

        Returns:
            int
                Current proposal dequeue frequency in seconds
        """
        return self._contract.functions.lastDequeue().call()

    def dequeue_frequency(self) -> int:
        """
        Query proposal dequeue frequency

        Returns:
            int
                Current proposal dequeue frequency in seconds
        """
        return self._contract.functions.dequeueFrequency().call()

    def min_deposit(self) -> int:
        """
        Query minimum deposit required to make a proposal

        Returns:
            int
                Current minimum deposit
        """
        return self._contract.functions.minDeposit().call()

    def queue_expiry(self) -> int:
        """
        Query queue expiry parameter

        Returns:
            int
                The number of seconds a proposal can stay in the queue before expiring
        """
        return self._contract.functions.queueExpiry().call()

    def stage_duration(self) -> dict:
        """
        Query durations of different stages in proposal lifecycle

        Returns:
            dict
                Durations for approval, referendum and execution stages in seconds
        """
        res = self._contract.functions.stageDurations().call()

        return {
            'approval': res[0],
            'referendum': res[1],
            'execution': res[2]
        }

    def get_transaction_constitution(self, tx_proposal: dict) -> int:
        """
        Returns the required ratio of yes:no votes needed to exceed in order to pass the proposal transaction

        Parameters:
            tx_proposal: dict {to: `address`, input: `str`, value: `str`}
                Transaction to determine the constitution for running
        Returns:
            int
        """
        call_signature = '0x' + (tx_proposal['input'].lstrip('0x')[0:8])
        destination = tx_proposal['to'] if tx_proposal['to'] else self.null_address

        return self._contract.functions.getConstitution(destination, call_signature)

    def get_constitution(self, proposal: List[dict]) -> int:
        """
        Returns the required ratio of yes:no votes needed to exceed in order to pass the proposal

        Parameters:
            proposal: list[{to: str, input: str, value: str}]
        """
        constitution = 0
        for tx in proposal:
            if c := self.get_transaction_constitution(tx) > constitution:
                constitution = c

        return constitution

    def get_participation_parameters(self) -> dict:
        """
        Returns the participation parameters

        Returns:
            dict
                The participation parameters
        """
        res = self._contract.functions.getParticipationParameters().call()

        return {
            'base_line': res[0],
            'base_line_floor': res[1],
            'base_line_update_factor': res[2],
            'base_line_quorum_factor': res[3]
        }

    def is_voting(self, account: str) -> bool:
        """
        Returns whether or not a particular account is voting on proposals

        Parameters:
            account: str
                The address of the account
        Returns:
            bool
                Whether or not the account is voting on proposals
        """
        return self._contract.functions.isVoting(account).call()

    def get_config(self) -> dict:
        """
        Returns current configuration parameters
        """
        concurrent_proposals = self.concurrent_proposals()
        dequeue_frequency = self.dequeue_frequency()
        min_deposit = self.min_deposit()
        queue_expiry = self.queue_expiry()
        stage_duration = self.stage_duration()
        participation_parameters = self.get_participation_parameters()

        return {
            'concurrent_proposals': concurrent_proposals,
            'dequeue_frequency': dequeue_frequency,
            'min_deposit': min_deposit,
            'queue_expiry': queue_expiry,
            'stage_duration': stage_duration,
            'participation_parameters': participation_parameters
        }

    def get_proposal_metadata(self, proposal_id: int) -> dict:
        """
        Returns the metadata associated with a given proposal

        Parameters:
            proposal_id: int
                Governance proposal UUID
        """
        res = self._contract.functions.getProposal(proposal_id).call()

        return {
            'proposer': res[0],
            'deposit': res[1],
            'timestamp': res[2],
            'transaction_count': res[3],
            'description_url': res[4]
        }

    def get_proposal_transaction(self, proposal_id: int, tx_index: int) -> dict:
        """
        Returns the transaction at the given index associated with a given proposal

        Parameters:
            proposal_id: int
                Governance proposal UUID
            tx_index: int
                Transaction index
        """
        res = self._contract.functions.getProposalTransaction(
            proposal_id, tx_index).call()

        return {
            'value': res[0],
            'to': res[1],
            'input': res[2]
        }

    def is_approved(self, proposal_id: int) -> bool:
        """
        Returns whether a given proposal is approved

        Parameters:
            proposal_id: int
                Governance proposal UUID
        """
        return self._contract.functions.isApproved(proposal_id).call()

    def is_dequeued_proposal_expired(self, proposal_id: int) -> bool:
        """
        Returns whether a dequeued proposal is expired

        Parameters:
            proposal_id: int
                Governance proposal UUID
        """
        return self._contract.functions.isDequeuedProposalExpired(proposal_id).call()

    def is_queued_proposal_expired(self, proposal_id: int) -> bool:
        """
        Returns whether a dequeued proposal is expired

        Parameters:
            proposal_id: int
                Governance proposal UUID
        """
        return self._contract.functions.isQueuedProposalExpired(proposal_id).call()

    def get_approver(self) -> str:
        """
        Returns the approver address for proposals and hotfixes
        """
        return self._contract.functions.approver().call()

    def get_proposal_stage(self, proposal_id: int) -> str:
        """
        Returns stage of proposal by it's id
        """
        return self.proposal_stage[self._contract.functions.getProposalStage(proposal_id).call()]

    def time_until_stages(self, proposal_id: int) -> dict:
        meta = self.get_proposal_metadata(proposal_id)
        now = int(time.time())
        durations = self.stage_duration()
        referendum = meta['timestamp'] + durations['approval'] - now
        execution = referendum + durations['referendum']
        expiration = execution + durations['execution']

        return {'referendum': referendum, 'execution': execution, 'expiration': expiration}

    def get_proposal(self, proposal_id: int) -> list:
        """
        Returns the proposal associated with a given id

        Parameters:
            proposal_id: int
                Governance proposal UUID
        """
        metadata = self.get_proposal_metadata(proposal_id)
        result = []

        for ind in range(metadata['transaction_count']):
            result.append(self.get_proposal_transaction(proposal_id, ind))

        return result

    def get_proposal_record(self, proposal_id: int) -> dict:
        """
        Returns the stage, metadata, upvotes, votes, and transactions associated with a given proposal

        Parameters:
            proposal_id: int
                Governance proposal UUID
        """
        metadata = self.get_proposal_metadata(proposal_id),
        proposal = self.get_proposal(proposal_id)
        stage = self.get_proposal_stage(proposal_id)
        passing = self.is_proposal_passing(proposal_id)

        upvotes = 0
        votes = {self.vote_value['yes']: 0, self.vote_value['no']: 0, self.vote_value['abstain']: 0}

        if stage == self.proposal_stage[1]:
            upvotes = self.get_upvotes(proposal_id)
        elif stage != self.proposal_stage[5]:
            votes = self.get_votes(proposal_id)

        return {
            'proposal': proposal,
            'metadata': metadata,
            'stage': stage,
            'upvotes': upvotes,
            'votes': votes,
            'passing': passing
        }

    def is_proposal_passing(self, proposal_id: int) -> bool:
        """
        Returns whether a given proposal is passing relative to the constitution's threshold

        Parameters:
            proposal_id: int
                Governance proposal UUID
        """
        return self._contract.functions.isProposalPassing(proposal_id).call()

    def withdraw(self) -> str:
        """
        Withdraws refunded proposal deposits
        """
        func_call = self._contract.functions.withdraw()

        return self.__wallet.send_transaction(func_call)

    def proposal_to_params(self, values: List[int], description_url: str) -> list:
        data = []
        for el in values:
            addr = el['input'].lstrip('0x')
            data.append([elem.encode("hex") for elem in addr])
        return [
            [el['value'] for el in values],
            [el['to'] for el in values if 'to' in el],
            self.web3.toBytes('0x'+bytes(data).hex()),
            [len(el) for el in data],
            description_url
        ]

    def propose(self, values: List[int], description_url: str, parameters: dict = None) -> int:
        data = self.proposal_to_params(values, description_url)

        func_call = self._contract.functions.propose(data[0], data[1], data[2], data[3], data[4])

        return self.__wallet.send_transaction(func_call, parameters)

    def proposal_exists(self, proposal_id: int) -> bool:
        """
        Returns whether a governance proposal exists with the given ID

        Parameters:
            proposal_id: int
                Governance proposal UUID
        """
        return self._contract.functions.proposalExists(proposal_id).call()

    def get_upvote_record(self, upvoter: str) -> dict:
        """
        Returns the current upvoted governance proposal ID and applied vote weight (zeroes if none)

        Parameters:
            upvoter: str
                Address of upvoter
        """
        res = self._contract.functions.getUpvoteRecord(upvoter).call()

        return {'proposal_id': res[0], 'upvotes': res[1]}

    def get_vote_record(self, voter: str, proposal_id: int) -> dict:
        """
        Returns the corresponding vote record

        Parameters:
            voter: str
                Address of voter
            proposal_id: int
                Governance proposal UUID
        """
        try:
            proposal_index = self._get_dequeue_index(proposal_id)
            res = self._contract.functions.getVoteRecord(
                voter, proposal_index).call()
            return {
                'proposal_id': res[0],
                'value': self.vote_value[list(self.vote_value.keys())[res[1]]],
                'votes': res[2]
            }
        except:
            return None

    def is_queued(self, proposal_id: int) -> bool:
        """
        Returns whether a given proposal is queued

        Parameters:
            proposal_id: int
                Governance proposal UUID
        """
        return self._contract.functions.isQueued(proposal_id).call()

    def get_refunded_deposits(self, proposer: str) -> int:
        """
        Returns the value of proposal deposits that have been refunded

        Parameters:
            proposer: str
                Governance proposer address
        """
        return self._contract.functions.refundedDeposits(proposer).call()

    def get_upvotes(self, proposal_id: str) -> int:
        """
        Returns the upvotes applied to a given proposal

        Parameters:
            proposal_id: str
                Governance proposal UUID
        """
        return self._contract.functions.getUpvotes(proposal_id).call()

    def get_votes(self, proposal_id: str) -> dict:
        """
        Returns the yes, no, and abstain votes applied to a given proposal

        Parameters:
            proposal_id: str
                Governance proposal UUID
        """
        res = self._contract.functions.getVoteTotals(proposal_id).call()

        return {self.vote_value['yes']: res[0], self.vote_value['no']: res[1], self.vote_value['abstain']: res[2]}

    def get_queue(self) -> List[dict]:
        """
        Returns the proposal queue as list of upvote records
        """
        res = self._contract.functions.getQueue().call()

        result = []

        length = min(len(res[0]), len(res[1]))

        for ind in range(length):
            result.append({'proposal_id': res[0][ind], 'upvotes': res[1][ind]})

        return result

    def get_dequeue(self, filter_zeroes: bool = False) -> list:
        """
        Returns the (existing) proposal dequeue as list of proposal IDs
        """
        dequeue = self._contract.functions.getDequeue().call()

        return dequeue if not filter_zeroes else [el for el in dequeue if el != 0]

    def get_vote_records(self, voter: str) -> List[dict]:
        """
        Returns the vote records for a given voter
        """
        dequeue = self.get_dequeue()
        vote_records = []

        for ind in dequeue:
            vote_records.append(self.get_vote_record(voter, ind))

        return [el for el in vote_records if vote_records != None]

    def get_voter(self, account: str) -> dict:
        """
        Returns information pertaining to a voter in governance
        """
        upvote_record = self.get_upvote_record(account)
        vote_records = self.get_vote_records(account)
        refunded_deposits = self.get_refunded_deposits(account)

        return {
            'upvote': upvote_record,
            'votes': vote_records,
            'refunded_deposits': refunded_deposits
        }

    def dequeue_proposals_if_ready(self) -> str:
        func_call = self._contract.functions.dequeueProposalsIfReady()

        return self.__wallet.send_transaction(func_call)

    def get_vote_weight(self, voter: str) -> int:
        """
        Returns the number of votes that will be applied to a proposal for a given voter

        Parameters:
            voter: str
                Addres of voter
        """
        locked_gold_contract = self.create_and_get_contract_by_name(
            'LockedGold')

        return locked_gold_contract.get_account_total_locked_gold(voter)

    def _get_index(self, id: int, array: list) -> int:
        try:
            index = array.index(id)
            return index
        except:
            raise Exception(f"ID {id} not found in array {array}")

    def _get_dequeue_index(self, proposal_id: int, dequeue: List[int] = []) -> int:
        if not dequeue:
            dequeue = self.get_dequeue()
        return self._get_index(proposal_id, dequeue)

    def _get_queue_index(self, proposal_id: int, queue: List[dict] = []) -> dict:
        if not queue:
            queue = self.get_queue()
        return {
            'index': self._get_index(proposal_id, [el['proposal_id'] for el in queue]),
            'queue': queue
        }

    def _lesser_and_greater(self, proposal_id: int, queue: List[dict] = []) -> dict:
        index, queue = self._get_queue_index(proposal_id, queue)
        return {
            'lesser_id': 0 if index == 0 else queue[index - 1]['proposal_id'],
            'greater_id': 0 if index == len(queue) - 1 else queue[index + 1]['proposal_id']
        }

    def _sort_func(self, e):
        return e['proposal_id']

    def sorted_queue(self, queue: List[dict]) -> List[dict]:
        return queue.sort(key=self._sort_func)

    def _with_upvote_revoked(self, upvoter: str, queue_p: List[dict] = []) -> dict:
        upvoter_record = self.get_upvote_record(upvoter)
        index, queue = self._get_queue_index(
            upvoter_record['proposal_id'], queue_p).values()
        queue[index]['upvotes'] = queue[index]['upvotes'] - \
            upvoter_record['upvotes']

        return {'queue': self.sorted_queue(queue), 'upvote_record': upvoter_record}

    def _with_upvote_applied(self, upvoter: str, proposal_id: int, queue_p: List[dict] = []) -> list:
        index, queue = self._get_queue_index(proposal_id, queue_p).values()
        weight = self.get_vote_weight(upvoter)
        queue[index]['upvotes'] = queue[index]['upvotes'] + weight

        return self.sorted_queue(queue)

    def _lesser_and_greater_after_revoke(self, upvoter: str) -> dict:
        queue, upvote_record = self._with_upvote_revoked(upvoter).values()

        return self._lesser_and_greater(upvote_record['proposal_id'], queue)

    def _lesser_and_greater_after_upvote(self, upvoter: str, proposal_id: int) -> dict:
        upvote_record = self.get_upvote_record(upvoter)
        record_queued = self.is_queued(upvote_record['proposal_id'])
        queue = self._with_upvote_revoked(
            upvoter)['queue'] if record_queued else self.get_queue()
        upvote_queue = self._with_upvote_applied(upvoter, proposal_id, queue)

        return self._lesser_and_greater(proposal_id, upvote_queue)

    def upvote(self, proposal_id: int, upvoter: str, parameters: dict = None) -> str:
        """
        Applies provided upvoter's upvote to given proposal

        Parameters:
            proposal_id: int
                Governance proposal UUID
            upvoter: str
                Address of upvoter
        Returns:
            str
                Transaction hash
        """
        lesser_id, greater_id = self._lesser_and_greater_after_upvote(
            upvoter, proposal_id)

        func_call = self._contract.functions.upvote(
            proposal_id, lesser_id, greater_id)

        return self.__wallet.send_transaction(func_call, parameters)

    def revoke_upvote(self, upvoter: str, parameters: dict = None) -> str:
        """
        Revokes provided upvoter's upvote

        Parameters:
            upvotes: str
                Address of upvoter
        """
        lesser_id, greater_id = self._lesser_and_greater_after_revoke(upvoter)

        func_call = self._contract.functions.revokeUpvote(
            lesser_id, greater_id)

        return self.__wallet.send_transaction(func_call, parameters)

    def approve(self, proposal_id: int) -> str:
        """
        Approves given proposal, allowing it to later move to `referendum`

        Parameters:
            proposal_id: int
                Governance proposal UUID
        Returns:
            str
                Transaction hash
        """
        proposal_index = self._get_dequeue_index(proposal_id)

        func_call = self._contract.functions.approve(
            proposal_id, proposal_index)

        return self.__wallet.send_transaction(func_call)

    def vote(self, proposal_id: int, vote: str, parameters: dict = None) -> str:
        """
        Applies `sender`'s vote choice to a given proposal

        Parameters:
            proposal_id: int
                Governance proposal UUID
            vote: str
                Choice to apply (yes, no, abstain)
        Returns:
            str
                Transaction hash
        """
        proposal_index = self._get_dequeue_index(proposal_id)
        vote_num = list(self.vote_value.keys()).index(vote)

        func_call = self._contract.functions.vote(
            proposal_id, proposal_index, vote_num)

        return self.__wallet.send_transaction(func_call, parameters)

    def get_vote_value(self, proposal_id: int, voter: str) -> str:
        """
        Returns `voter`'s vote choice on a given proposal

        Parameters:
            proposal_id: int
                Governance proposal UUID
            voter: str
                Address of voter
        """
        proposal_index = self._get_dequeue_index(proposal_id)
        res = self._contract.functions.getVoteRecord(
            voter, proposal_index).call()

        return list(self.vote_value.keys())[res[1]]

    def execute(self, proposal_id: int) -> str:
        """
        Executes a given proposal's associated transactions

        Parameters:
            proposal_id: int
                Governance proposal UUID
        Returns:
            str
                Transaction hash
        """
        proposal_index = self._get_dequeue_index(proposal_id)

        func_call = self._contract.functions.execute(
            proposal_id, proposal_index)

        return self.__wallet.send_transaction(func_call)

    def get_hotfix_record(self, hash: str) -> dict:
        """
        Returns approved, executed, and prepared status associated with a given hotfix

        Parameters:
            hash: bytes
                keccak256 hash of hotfix's associated abi encoded transactions
        """
        res = self._contract.functions.getHotfixRecord(hash).call()

        return {'approved': res[0], 'executed': res[1], 'prepared_epoch': res[2]}

    def is_hotfix_whitelisted_by(self, hash: str, whitelister: str) -> bool:
        """
        Returns whether a given hotfix has been whitelisted by a given address

        Parameters:
            hash: str
                keccak256 hash of hotfix's associated abi encoded transactions
            whitelister: str
                address of whitelister
        """
        return self._contract.functions.isHotfixWhitelistedBy(hash, whitelister).call()

    def is_hotfix_passing(self, hash: str) -> bool:
        """
        Returns whether a given hotfix can be passed

        Parameters:
            hash: str
                keccak256 hash of hotfix's associated abi encoded transactions
        """
        return self._contract.functions.isHotfixPassing(hash).call()

    def min_quorum_size(self) -> int:
        """
        Returns the number of validators required to reach a Byzantine quorum
        """
        return self._contract.functions.minQuorumSizeInCurrentSet().call()

    def hotfix_whitelist_validator_tally(self, hash: str) -> int:
        """
        Returns the number of validators that whitelisted the hotfix

        Parameters:
            hash: str
                keccak256 hash of hotfix's associated abi encoded transactions
        """
        return self._contract.functions.hotfixWhitelistValidatorTally(hash).call()

    def whitelist_hotfix(self, hash: str) -> str:
        """
        Marks the given hotfix whitelisted by `sender`

        Parameters:
            hash: str
                keccak256 hash of hotfix's associated abi encoded transactions
        Returns:
            str
                Transaction hash
        """
        func_call = self._contract.functions.whitelistHotfix(hash)

        return self.__wallet.send_transaction(func_call)

    def approve_hotfix(self, hash: str) -> str:
        """
        Marks the given hotfix approved by `sender`

        Parameters:
            hash: str
                keccak256 hash of hotfix's associated abi encoded transactions
        Returns:
            str
                Transaction hash
        """
        func_call = self._contract.functions.approveHotfix(hash)

        return self.__wallet.send_transaction(func_call)

    def prepare_hotfix(self, hash: str) -> str:
        """
        Marks the given hotfix prepared for current epoch if quorum of validators have whitelisted it

        Parameters:
            hash: str
                keccak256 hash of hotfix's associated abi encoded transactions
        Returns:
            str
                Transaction hash
        """
        func_call = self._contract.functions.prepareHotfix(hash)

        return self.__wallet.send_transaction(func_call)

    def execute_hotfix(self, values: List[int], destinations: List[str], data: str, data_lengths: List[int], salt: str) -> str:
        """
        Executes a given sequence of transactions if the corresponding hash is prepared and approved

        Parameters:
            values: List[int]
            destinations: List[str]
                List of addresses
            data: str
            data_lengths: List[int]
            salt: str
        """
        func_call = self._contract.functions.executeHotfix(
            values, destinations, data, data_lengths, salt)

        return self.__wallet.send_transaction(func_call)
