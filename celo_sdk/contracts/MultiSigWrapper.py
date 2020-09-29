import time
from typing import List

from web3 import Web3

from celo_sdk.contracts.base_wrapper import BaseWrapper
from celo_sdk.registry import Registry


class MultiSig(BaseWrapper):
    """
    Contract for handling multisig actions

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

    def submit_or_confirm_transaction(self, destination: str, tx_data: str, value: int = 0, parameters: dict = None) -> str:
        """
        Allows an owner to submit and confirm a transaction.
        If an unexecuted transaction matching `tx_object` exists on the multisig, adds a confirmation to that tx ID.
        Otherwise, submits the `tx_object` to the multisig and add confirmation.

        Parameters:
            destination: str
            tx_object: str
                Transaction data hex string
            value: str
        Returns:
            str
                Transaction hash
        """
        # sure that data start with 0x
        data = '0x' + tx_data.lstrip('0x')
        transaction_count = self._contract.functions.getTransactionCount(
            True, True).call()

        for tx_id in reversed(range(transaction_count)):
            transaction = self._contract.functions.transactions(
                tx_id + 1).call()
            if transaction[2] == data and transaction[0] == destination and transaction[1] == value and not transaction[3]:
                func_call = self._contract.functions.confirmTransaction(
                    tx_id + 1)
                return self.__wallet.send_transaction(func_call, parameters)

        func_call = self._contract.functions.submitTransaction(
            destination, value, tx_data)

        return self.__wallet.send_transaction(func_call, parameters)

    def is_owner(self, owner: str) -> bool:
        return self._contract.functions.isOwner(owner).call()

    def get_owners(self) -> List[str]:
        return self._contract.functions.getOwners().call()

    def get_required(self) -> int:
        return self._contract.functions.required().call()

    def get_internal_required(self) -> int:
        return self._contract.functions.internalRequired().call()

    def get_transaction_count(self) -> int:
        return self._contract.functions.transactionCount().call()

    def replace_owner(self, owner: str, new_owner: str) -> str:
        func_call = self._contract.functions.replaceOwner(owner, new_owner)

        return self.__wallet.send_transaction(func_call)

    def get_transaction(self, i: int) -> dict:
        destination, value, data, executed = self._contract.functions.transactions(
            i).call()

        confirmations = []
        for owner in self.get_owners():
            if self._contract.functions.confirmations(i, owner).call():
                confirmations.append(owner)

        return {
            'destination': destination,
            'data': data,
            'executed': executed,
            'confirmations': confirmations,
            'value': value
        }

    def get_transactions(self) -> List[dict]:
        tx_count = self.get_transaction_count()
        res = []
        for i in range(tx_count):
            res.append(self.get_transaction(i))

        return res
