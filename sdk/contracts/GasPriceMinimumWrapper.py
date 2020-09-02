import sys

from sdk.wallet import Wallet

from web3 import Web3


class GasPriceMinimum:
    def __init__(self, web3: Web3, address: str, abi: list, wallet: Wallet = None):
        self.web3 = web3
        self.address = address
        self._contract = self.web3.eth.contract(self.address, abi=abi)
        self.__wallet = wallet

    def get_price_minimum(self) -> int:
        try:
            gas_price = self._contract.functions.gasPriceMinimum().call()
            return gas_price
        except:
            raise Exception(
                f"Unexpected error occurs while get gas price from GasPriceMinimum smart contract:\n{sys.exc_info()[1]}")

    def get_gas_price_minimum(self, address: str) -> int:
        try:
            gas_price = self._contract.functions.getGasPriceMinimum(
                address).call()
            return gas_price
        except:
            raise Exception(
                f"Unexpected error occurs while get gas price in certain token from GasPriceMinimum smart contract:\n{sys.exc_info()[1]}")

    def target_density(self) -> int:
        try:
            target_density = self._contract.functions.targetDensity().call()
            return target_density
        except:
            raise Exception(
                f"Unexpected error occurs while get target density from GasPriceMinimum smart contract:\n{sys.exc_info()[1]}")

    def adjustment_speed(self) -> int:
        try:
            adjustment_speed = self._contract.functions.adjustmentSpeed().call()
            return adjustment_speed
        except:
            raise Exception(
                f"Unexpected error occurs while get adjustment speed from GasPriceMinimum smart contract:\n{sys.exc_info()[1]}")

    def get_config(self) -> dict:
        pass
