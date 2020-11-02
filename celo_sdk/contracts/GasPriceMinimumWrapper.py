import sys

from web3 import Web3


class GasPriceMinimum:
    """
    Stores the gas price minimum

    Attributes:
        web3: Web3
            Web3 object
        address: str
            Contract's address
        abi: list
            Contract's ABI
        wallet: Wallet
            Wallet object to sign transactions
    """

    def __init__(self, web3: Web3, address: str, abi: list, wallet: 'Wallet' = None, **kwargs):
        self.web3 = web3
        self.address = address
        self._contract = self.web3.eth.contract(self.address, abi=abi)
        self.__wallet = wallet

    def get_price_minimum(self) -> int:
        return self._contract.functions.gasPriceMinimum().call()

    def get_gas_price_minimum(self, address: str) -> int:
        return self._contract.functions.getGasPriceMinimum(address).call()

    def target_density(self) -> int:
        return self._contract.functions.targetDensity().call()

    def adjustment_speed(self) -> int:
        return self._contract.functions.adjustmentSpeed().call()

    def get_config(self) -> dict:
        gas_price_minimum = self.get_price_minimum()
        target_density = self.target_density()
        adjustment_speed = self.adjustment_speed()

        return {
            'gas_price_minimum': gas_price_minimum,
            'target_density': target_density,
            'adjustment_speed': adjustment_speed
        }
