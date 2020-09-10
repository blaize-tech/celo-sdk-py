import sys

from sdk.contracts.base_wrapper import BaseWrapper
from sdk.registry import Registry

from web3 import Web3


# TODO: test when other called SC wrappers will be written and callable
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
    
    def get_epoch_number_of_block(self, block: int) -> int:
        pass