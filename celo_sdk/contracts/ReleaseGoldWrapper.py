import sys
import time
from typing import List

from eth_keys.datatypes import PublicKey
from web3 import Web3

from celo_sdk.contracts.base_wrapper import BaseWrapper
from celo_sdk.celo_account.account import Account
from celo_sdk.celo_account.messages import encode_defunct
from celo_sdk.registry import Registry
from celo_sdk.utils import hash_utils


class ReleaseGold(BaseWrapper):
    """
    Contract for handling an instance of a ReleaseGold contract

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

    def get_release_schedule(self) -> dict:
        """
        Returns the underlying Release schedule of the ReleaseGold contract
        """
        release_schedule = self._contract.functions.releaseSchedule().call()

        return {
            'release_start_time': release_schedule[0],
            'release_cliff': release_schedule[1],
            'num_release_periods': release_schedule[2],
            'release_period': release_schedule[3],
            'amount_released_per_period': release_schedule[4]
        }

    def get_beneficiary(self) -> str:
        """
        Returns the beneficiary of the ReleaseGold contract

        Returns:
            str
                The address of the beneficiary
        """
        return self._contract.functions.beneficiary().call()

    def get_release_owner(self) -> str:
        """
        Returns the releaseOwner address of the ReleaseGold contract

        Returns:
            str
                The address of the releaseOwner
        """
        return self._contract.functions.releaseOwner().call()

    def get_refund_address(self) -> str:
        """
        Returns the refund address of the ReleaseGold contract

        Returns:
            str
                The refundAddress
        """
        return self._contract.functions.refundAddress().call()

    def get_owner(self) -> str:
        """
        Returns the owner's address of the ReleaseGold contract

        Returns:
            str
                The owner's address
        """
        return self._contract.functions.owner().call()

    def get_liquidity_provision_met(self) -> bool:
        """
        Returns true if the liquidity provision has been met for this contract

        Returns:
            bool
                If the liquidity provision is met
        """
        return self._contract.functions.liquidityProvisionMet().call()

    def get_can_validate(self) -> bool:
        """
        Returns true if the contract can validate

        Returns:
            bool
                If the contract can validate
        """
        return self._contract.functions.canValidate().call()

    def get_can_vote(self) -> bool:
        """
        Returns true if the contract can vote

        Returns:
            bool
                If the contract can vote
        """
        return self._contract.functions.canVote().call()

    def get_total_withdrawn(self) -> int:
        """
        Returns the total withdrawn amount from the ReleaseGold contract

        Returns:
            int
                The total withdrawn amount from the ReleaseGold contract
        """
        return self._contract.functions.totalWithdrawn().call()

    def get_max_distribution(self) -> int:
        """
        Returns the maximum amount of gold (regardless of release schedule)
        currently allowed for release

        Returns:
            int
                The max amount of gold currently withdrawable
        """
        return self._contract.functions.maxDistribution().call()

    def get_revocation_info(self) -> dict:
        """
        Returns the underlying Revocation Info of the ReleaseGold contract

        Returns:
            dict
                A RevocationInfo dict
        """
        try:
            revocation_info = self._contract.functions.revocationInfo().call()
            return {
                'revocable': revocation_info[0],
                'can_expire': revocation_info[1],
                'released_balance_at_revoke': revocation_info[2],
                'revoke_time': revocation_info[3]
            }
        except:
            return {
                'revocable': False,
                'can_expire': False,
                'released_balance_at_revoke': 0,
                'revoke_time': 0
            }

    def is_revocable(self) -> bool:
        """
        Indicates if the release grant is revocable or not

        Returns:
            bool
                A boolean indicating revocable releasing (true) or non-revocable(false)
        """
        revocation_info = self.get_revocation_info()

        return revocation_info['revocable']

    def is_revoked(self) -> bool:
        """
        Indicates if the release grant is revoked or not

        Returns:
            bool
                A boolean indicating revoked releasing (true) or non-revoked(false)
        """
        return self._contract.functions.isRevoked().call()

    def get_revoke_time(self) -> int:
        """
        Returns the time at which the release schedule was revoked

        Returns:
            int
                The timestamp of the release schedule revocation
        """
        revocation_info = self.get_revocation_info()

        return revocation_info['revoke_time']

    def get_released_balance_at_revoke(self) -> int:
        """
        Returns the balance of released gold when the grant was revoked

        Returns:
            int
                The balance at revocation time. 0 can also indicate not revoked
        """
        revocation_info = self.get_revocation_info()

        return revocation_info['released_balance_at_revoke']

    def get_total_balance(self) -> int:
        """
        Returns the total balance of the ReleaseGold instance

        Returns:
            int
                The total ReleaseGold instance balance
        """
        return self._contract.functions.getTotalBalance().call()

    def get_remaining_total_balance(self) -> int:
        """
        Returns the the sum of locked and unlocked gold in the ReleaseGold instance

        Returns:
            int
                The remaining total ReleaseGold instance balance
        """
        return self._contract.functions.getRemainingTotalBalance().call()

    def get_remainimg_unlocked_balance(self) -> int:
        """
        Returns the remaining unlocked gold balance in the ReleaseGold instance

        Returns:
            int
                The available unlocked ReleaseGold instance gold balance
        """
        return self._contract.functions.getRemainingUnlockedBalance().call()

    def get_remaining_locked_balance(self) -> int:
        """
        Returns the remaining locked gold balance in the ReleaseGold instance

        Returns:
            int
                The remaining locked ReleaseGold instance gold balance
        """
        return self._contract.functions.getRemainingLockedBalance().call()

    def get_current_released_total_amount(self) -> int:
        """
        Returns the total amount that has already released up to now

        Returns:
            int
                The already released gold amount up to the point of call
        """
        return self._contract.functions.getCurrentReleasedTotalAmount().call()

    def revoke_releasing(self) -> str:
        """
        Revoke a Release schedule

        Returns:
            str
                Transaction hash
        """
        func_call = self._contract.functions.revoke()

        return self.__wallet.send_transaction(func_call)

    def refund_and_finalize(self) -> str:
        """
        Refund `refundAddress` and `beneficiary` after the ReleaseGold schedule has been revoked

        Returns:
            str
                Transaction hash
        """
        func_call = self._contract.functions.refundAndFinalize()

        return self.__wallet.send_transaction(func_call)

    def lock_gold(self, value: int) -> str:
        """
        Locks gold to be used for voting

        Parameters:
            value: int
                The amount of gold to lock
        Returns:
            str
                Transaction hash
        """
        func_call = self._contract.functions.lockGold(value)

        return self.__wallet.send_transaction(func_call)

    def transfer(self, to: str, value: int) -> str:
        """
        Parameters:
            to: str
            value: int
        Returns:
            str
                Transaction hash
        """
        func_call = self._contract.functions.transfer(to, value)

        return self.__wallet.send_transaction(func_call)

    def unlock_gold(self, value: int) -> str:
        """
        Unlocks gold that becomes withdrawable after the unlocking period

        Parameters:
            value: int
                The amount of gold to unlock
        Returns:
            str
                Transaction hash
        """
        func_call = self._contract.functions.unlockGold(value)

        return self.__wallet.send_transaction(func_call)

    def relock_gold(self, value: int) -> List[str]:
        """
        Relocks gold in the ReleaseGold instance that has been unlocked but not withdrawn

        Parameters:
            value: int
                The value to relock from the specified pending withdrawal
        """
        locked_gold_contract = self.create_and_get_contract_by_name(
            'LockedGold')
        pending_withdrawals = locked_gold_contract.get_pending_withdrawals(
            self.__wallet.active_account.address)
        total_value = locked_gold_contract.get_pending_withdrawals_total_value(
            self.__wallet.active_account.address)

        if total_value < value:
            raise Exception(
                f"Not enough pending withdrawals to relock {value}")

        for ind, withd in enumerate(pending_withdrawals):
            if ind != 0:
                if not withd['time'] >= pending_withdrawals[ind - 1]['time']:
                    raise Exception(
                        "Pending withdrawals not sorted by timestamp")

        remaining_to_relock = value

        res = []
        for ind in reversed(range(len(pending_withdrawals))):
            value_to_relock = min(
                pending_withdrawals[ind]['value'], remaining_to_relock)
            if value_to_relock > 0:
                remaining_to_relock -= value_to_relock
                res.append(self._relock_gold(ind, value_to_relock))

        return res

    def _relock_gold(self, index: int, value: int) -> str:
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
        func_call = self._contract.functions.relockGold(index, value)

        return self.__wallet.send_transaction(func_call)

    def withdraw_locked_gold(self, index: int) -> str:
        """
        Withdraw gold in the ReleaseGold instance that has been unlocked but not withdrawn

        Parameters:
            index: int
                The index of the pending locked gold withdrawal
        Returns:
            str
                Transaction hash
        """
        func_call = self._contract.functions.withdrawLockedGold(index)

        return self.__wallet.send_transaction(func_call)

    def withdraw(self, value: int) -> str:
        """
        Transfer released gold from the ReleaseGold instance back to beneficiary

        Parameters:
            value: int
                The requested gold amount
        Returns:
            str
                Transaction hash
        """
        func_call = self._contract.functions.withdraw(value)

        return self.__wallet.send_transaction(func_call)

    def create_account(self) -> str:
        """
        Beneficiary creates an account on behalf of the ReleaseGold contract
        """
        func_call = self._contract.functions.createAccount()

        return self.__wallet.send_transaction(func_call)

    def set_account(self, name: str, data_encryption_key: bytes, wallet_address: str, v: int, r: 'HexBytes', s: 'HexBytes') -> str:
        """
        Beneficiary creates an account on behalf of the ReleaseGold contract

        Parameters:
            name: str
            data_encryption_key: bytes
            wallet_address: str
            v: int
            r: 'HexBytes'
            s: 'HexBytes'
        Returns:
            str
                Transaction hash
        """
        func_call = self._contract.functions.setAccount(
            name, data_encryption_key, wallet_address, v, r, s)

        return self.__wallet.send_transaction(func_call)

    def set_account_name(self, name: str) -> str:
        """
        Set the name for the account

        Parameters:
            name: str
        Returns:
            str
                Transaction hash
        """
        func_call = self._contract.functions.setAccountName(name)

        return self.__wallet.send_transaction(func_call)

    def set_account_metadata_url(self, metadata_url: str) -> str:
        """
        Sets the metadataURL for the account

        Parameters:
            metadata_url: str
        Returns:
            str
                Transaction hash
        """
        func_call = self._contract.functions.setAccountMetadataURL(
            metadata_url)

        return self.__wallet.send_transaction(func_call)

    def set_account_wallet_address(self, wallet_address: str, v: int, r: 'HexBytes', s: 'HexBytes') -> str:
        """
        Sets the wallet address for the account
        Parameters:
            wallet_address: str
            v: int
            r: 'HexBytes'
            s: 'HexBytes'
        Returns:
            str
                Transaction hash
        """
        func_call = self._contract.functions.setAccountWalletAddress(
            wallet_address, v, r, s)

        return self.__wallet.send_transaction(func_call)

    def set_account_data_encryption_key(self, data_encryption_key: bytes) -> str:
        """
        Sets the data encryption of the account

        Parameters:
            data_encryption_key: bytes
        Returns:
            str
                Transaction hash
        """
        func_call = self._contract.functions.setAccountDataEncryptionKey(
            data_encryption_key)

        return self.__wallet.send_transaction(func_call)

    def set_liquidity_provision(self) -> str:
        """
        Sets the contract's liquidity provision to true
        """
        func_call = self._contract.functions.setLiquidityProvision()

        return self.__wallet.send_transaction(func_call)

    def set_can_expire(self, can_expire: bool) -> str:
        """
        Sets the contract's `canExpire` field to `canExpire`

        Parameters:
            can_expire: bool
                If the contract can expire `EXPIRATION_TIME` after the release schedule finishes
        Returns:
            str
                Transaction hash
        """
        func_call = self._contract.functions.setCanExpire(can_expire)

        return self.__wallet.send_transaction(func_call)

    def set_max_distribution(self, distribution_ratio: int) -> str:
        """
        Sets the contract's max distribution

        Parameters:
            distribution_ratio: int
        Returns:
            str
                Transaction hash
        """
        func_call = self._contract.functions.setMaxDistribution(
            distribution_ratio)

        return self.__wallet.send_transaction(func_call)

    def set_beneficiary(self, new_beneficiary: str) -> str:
        """
        Sets the contract's beneficiary

        Parameters:
            new_beneficiary: str
        Returns:
            str
                Transaction hash
        """
        func_call = self._contract.functions.setBeneficiary(new_beneficiary)

        return self.__wallet.send_transaction(func_call)

    def authorize_vote_signer(self, signer: str, signature: 'Signature') -> str:
        """
        Authorizes an address to sign votes on behalf of the account

        Parameters:
            signer: str
            signature: Signature object
        Returns:
            str
                Transaction hash
        """
        func_call = self._contract.functions.authorizeVoteSigner(
            signer, signature.v, self.web3.toBytes(signature.r), self.web3.toBytes(signature.s))

        return self.__wallet.send_transaction(func_call)

    def authorize_validator_signer(self, signer: str, proof_of_signing_key_possession: 'Signature') -> str:
        """
        Authorizes an address to sign validation messages on behalf of the account

        Parameters:
            signer: str
                The address of the validator signing key to authorize
            proof_of_signing_key_possession: Signature object
                The account address signed by the signer address
        Returns:
            str
                Transaction hash
        """
        validators_contract = self.create_and_get_contract_by_name(
            'Validators')
        account = self.__wallet.active_account.address

        if validators_contract.is_validator(account):
            message = self.web3.soliditySha3(['address'], [account]).hex()
            prefixed_msg = hash_utils.hash_message_with_prefix(
                self.web3, message)
            prefixed_msg = encode_defunct(hexstr=prefixed_msg)
            pub_key = Account.recover_hash_to_pub(prefixed_msg, vrs=proof_of_signing_key_possession.vrs).to_hex()
            func_call = self._contract.functions.authorizeValidatorSignerWithPublicKey(
                signer, proof_of_signing_key_possession.v, self.web3.toBytes(proof_of_signing_key_possession.r), self.web3.toBytes(proof_of_signing_key_possession.s), pub_key)

            return self.__wallet.send_transaction(func_call)
        else:
            func_call = self._contract.functions.authorizeValidatorSigner(
                signer, proof_of_signing_key_possession.v, self.web3.toBytes(proof_of_signing_key_possession.r), self.web3.toBytes(proof_of_signing_key_possession.s))

            return self.__wallet.send_transaction(func_call)

    def authorize_validator_signer_and_bls(self, signer: str, proof_of_signing_key_possession: 'Signature', bls_pub_key: str, bls_pop: str) -> str:
        """
        Authorizes an address to sign consensus messages on behalf of the contract's account. Also switch BLS key at the same time

        Parameters:
            signer: str
                The address of the signing key to authorize
            proof_of_signing_key_possession: Signature object
                The contract's account address signed by the signer address
            bls_pub_key: str
                The BLS public key that the validator is using for consensus, should pass proof
                of possession. 48 bytes
            bls_pop: str
                The BLS public key proof-of-possession, which consists of a signature on the
                account address. 96 bytes
        Returns:
            str
                Transaction hash
        """
        account = self.__wallet.active_account.address
        message = self.web3.soliditySha3(['address'], [account]).hex()
        prefixed_msg = hash_utils.hash_message_with_prefix(self.web3, message)
        prefixed_msg = encode_defunct(hexstr=prefixed_msg)
        pub_key = Account.recover_hash_to_pub(prefixed_msg, vrs=proof_of_signing_key_possession.vrs).to_hex()
        func_call = self._contract.functions.authorizeValidatorSignerWithKeys(
            signer, proof_of_signing_key_possession.v, self.web3.toBytes(proof_of_signing_key_possession.r), self.web3.toBytes(proof_of_signing_key_possession.s), pub_key, bls_pub_key, bls_pop)

        return self.__wallet.send_transaction(func_call)

    def authorize_attestation_signer(self, signer: str, proof_of_signing_key_possession: 'Signature') -> str:
        """
        Authorizes an address to sign attestation messages on behalf of the account

        Parameters:
            signer: str
                The address of the attestation signing key to authorize
            proof_of_signing_key_possession: Signature object
                The account address signed by the signer address
        Returns:
            str
                Transaction hash
        """
        func_call = self._contract.functions.authorizeAttestationSigner(
            signer, proof_of_signing_key_possession.v, self.web3.toBytes(proof_of_signing_key_possession.r), self.web3.toBytes(proof_of_signing_key_possession.s))

        return self.__wallet.send_transaction(func_call)

    def revoke_pending(self, account: str, group: str, value: int) -> str:
        """
        Revokes pending votes

        Parameters:
            account: str
                The account to revoke from
            group: str
                The group to revoke the vote for
            value: int
                The amount of gold to revoke
        Returns:
            str
                Transaction hash
        """
        try:
            election_contract = self.create_and_get_contract_by_name(
                'Election')
            groups = election_contract.get_groups_voted_for_by_account(account)
            index = groups.index(group)
            lesser_greater = election_contract.find_lesser_and_greater_after_vote(
                group, value * -1)
            func_call = self._contract.functions.revokePending(
                group, value, lesser_greater['lesser'], lesser_greater['greater'], index)

            return self.__wallet.send_transaction(func_call)
        except ValueError:
            raise Exception(
                f"There is no such group: {group} in groups voted for by account {account}")
        except:
            raise Exception(sys.exc_info())

    def revoke_active(self, account: str, group: str, value: int) -> str:
        """
        Revokes active votes

        Parameters:
            account: str
                The account to revoke from
            group: str
                The group to revoke the vote for
            value: int
                The amount of gold to revoke
        Returns:
            str
                Transaction hash
        """
        election_contract = self.create_and_get_contract_by_name('Election')
        groups = election_contract.get_groups_voted_for_by_account(account)
        index = groups.index(group)
        lesser_greater = election_contract.find_lesser_and_greater_after_vote(
            group, value * -1)

        func_call = self._contract.functions.revokeActive(
            group, value, lesser_greater['lesser'], lesser_greater['greater'], index)

        return self.__wallet.send_transaction(func_call)

    def revoke(self, account: str, group: str, value: int) -> List[str]:
        election_contract = self.create_and_get_contract_by_name('Election')
        vote = election_contract.get_votes_for_group_by_account(account, group)

        if value > vote['pending'] + vote['active']:
            raise Exception(
                f"Can't revoke more votes for {group} than have been made by {account}")

        txos = []
        pending_value = min(vote['pending'], value)

        if pending_value > 0:
            txos.append(self.revoke_pending(account, group, pending_value))
        if pending_value < value:
            active_value = value - pending_value
            txos.append(self.revoke_active(account, group, active_value))
        
        return txos
