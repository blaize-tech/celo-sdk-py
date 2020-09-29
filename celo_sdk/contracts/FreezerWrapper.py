import sys

from celo_sdk.contracts.base_wrapper import BaseWrapper
from celo_sdk.registry import Registry

from web3 import Web3


class Freezer(BaseWrapper):
    """
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

    def freeze(self, target: str):
        return self._contract.functions.freeze(target).call()
    
    def unfreeze(self, target: str):
        return self._contract.functions.unfreeze(target).call()
    
    def is_frozen(self, address: str) -> bool:
        return self._contract.functions.isFrozen(address).call()
