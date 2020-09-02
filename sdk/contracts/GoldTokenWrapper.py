import sys

from sdk.wallet import Wallet

from web3 import Web3


class GoldToken:
    def __init__(self, web3: Web3, address: str, abi: list, wallet: Wallet = None):
        self.web3 = web3
        self.address = address
        self._contract = self.web3.eth.contract(self.address, abi=abi)
        self.__wallet = wallet

    def allowance(self, from_addr: str, to_addr: str) -> int:
        """
        Querying allowance

        Parameters:
            from_addr: str
                account who has given the allowance
            to_addr: str
                address of account to whom the allowance was given
        Returns:
            amount of allowance
        """
        try:
            pass
        except:
            pass

    def name(self) -> str:
        """
        Returns name of token
        """
        try:
            return self._contract.functions.name().call()
        except:
            raise Exception(
                f"Error while query name of token:\n{sys.exc_info()[1]}")
