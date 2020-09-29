import sys

from celo_sdk.contracts.base_wrapper import BaseWrapper
from celo_sdk.registry import Registry

from web3 import Web3


class Escrow(BaseWrapper):
    """
    Contract for handling reserve for stable currencies

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
    
    def excrowed_payments(self) -> list:
        return self._contract.functions.escrowedPayments().call()

    def received_payment_ids(self, first_param: bytes, second_param: int) -> str:
        return self._contract.functions.receivedPaymentIds(first_param, second_param).call()
    
    def sent_paymet_ids(self, address: str, payment_ids: int) -> str:
        return self._contract.functions.sentPaymentIds(address, payment_ids).call()

    def get_received_payment_ids(self, identifier: bytes) -> list:
        return self._contract.functions.getReceivedPaymentIds(identifier).call()
    
    def get_sent_payment_ids(self, sender: str) -> list:
        return self._contract.functions.getSentPaymentIds(sender).call()

    def transfer(self, from_addr: str, identifier: bytes, token: str, value: int, payment_id: str, min_attestations: int) -> str:
        func_call = self._contract.functions.transfer(from_addr, identifier, token, value, payment_id, min_attestations)

        return self.__wallet.send_transaction(func_call)
    
    def withdraw(self, payment_id: str, v: int, r: int, s: int) -> str:
        func_call = self._contract.functions.withdraw(payment_id, v, r, s)

        return self.__wallet.send_transaction(func_call)
    
    def revoke(self, payment_id: str) -> str:
        func_call = self._contract.functions.revoke(payment_id)

        return self.__wallet.send_transaction(func_call)