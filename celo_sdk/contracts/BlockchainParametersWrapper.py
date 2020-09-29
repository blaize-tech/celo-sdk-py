import sys

from web3 import Web3

from celo_sdk.contracts.base_wrapper import BaseWrapper
from celo_sdk.registry import Registry


class BlockchainParameters(BaseWrapper):
    """
    Network parameters that are configurable by governance

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
    
    def set_intrinsic_gas_for_alternative_fee_currency(self, gas: int) -> str:
        """
        Setting the extra intrinsic gas for transactions, where gas is paid using non-gold currency

        Parameters:
            gas: int
        Returns:
            Transaction hash
        """
        func_call = self._contract.functions.setIntrinsicGasForAlternativeFeeCurrency(gas)
        return self.__wallet.send_transaction(func_call)

    def get_block_gas_limit(self) -> int:
        """
        Getting the block gas limit
        """
        return self._contract.functions.blockGasLimit().call()

    def set_block_gas_limit(self, gas_limit: int) -> str:
        """
        Setting the block gas limit

        Parameters:
            gas_limit: int
        Returns:
            Transaction hash
        """
        func_call = self._contract.functions.setBlockGasLimit(gas_limit)
        return self.__wallet.send_transaction(func_call)

    def set_minimum_client_version(self, major: float, minor: float, patch: float) -> str:
        """
        Set minimum client version

        Parameters:
            major: float
            minor: float
            patch: float
        Returns:
            Transaction hash
        """
        func_call = self._contract.functions.setMinimumClientVersion()
        return self.__wallet.send_transaction(func_call)
