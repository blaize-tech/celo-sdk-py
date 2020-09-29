import sys

from celo_sdk.contracts.base_wrapper import BaseWrapper
from celo_sdk.registry import Registry

from web3 import Web3


class GoldToken(BaseWrapper):
    """
    Class which wrapp all the methods of GoldToken smart contract

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
        return self._contract.functions.allowance(from_addr, to_addr).call()

    def name(self) -> str:
        """
        Returns name of token
        """
        return self._contract.functions.name().call()

    def symbol(self) -> str:
        """
        Returns symbol of token

        Returns:
            str
        """
        return self._contract.functions.symbol().call()

    def decimals(self) -> int:
        """
        The number of decimal places to which StableToken is divisible

        Returns:
            int
        """
        return self._contract.functions.decimals().call()

    def total_supply(self) -> int:
        """
        Returns the total supply of the token, that is, the amount of tokens currently minted

        Returns:
            int
        """
        return self._contract.functions.totalSupply().call()

    def approve(self, spender: str, value: int) -> str:
        """
        Approve a user to transfer CELO on behalf of another user

        Parameters:
            spender: str
                The address which is being approved to spend CELO
            value: int
                The increment of the amount of CELO approved to the spender
        Returns:
            Transaction hash
        """
        func_call = self._contract.functions.approve(spender, value)
        return self.__wallet.send_transaction(func_call)

    def increase_allowance(self, spender: str, value: int) -> str:
        """
        Increases the allowance of another user

        Parameters:
            spender: str
                The address which is being approved to spend CELO
            value: int
                The increment of the amount of CELO approved to the spender
        Returns:
            Transaction hash
        """
        func_call = self._contract.functions.increaseAllowance(spender, value)
        return self.__wallet.send_transaction(func_call)

    def decrease_allowance(self, spender: str, value: int) -> str:
        """
        Decreases the allowance of another user

        Parameters:
            spender: str
                The address which is being approved to spend CELO
            value: int
                The decrement of the amount of CELO approved to the spender
        Returns:
            Transaction hash
        """
        func_call = self._contract.functions.decreaseAllowance(spender, value)
        return self.__wallet.send_transaction(func_call)

    def transfer_with_comment(self, to: str, value: int, comment: str) -> str:
        """
        Transfers CELO from one address to another with a comment

        Parameters:
            to: str
                The address to transfer CELO to
            value: int
                The amount of CELO to transfer
            comment: str
                The transfer comment
        Returns:
            Transaction hash
        """
        func_call = self._contract.functions.transferWithComment()
        return self.__wallet.send_transaction(func_call)
    
    def transfer(self, to: str, value: int) -> str:
        """
        Transfers CELO from one address to another

        Parameters:
            to: str
                The address to transfer CELO to
            value: int
                The amount of CELO to transfer
        Returns:
            Transaction hash
        """
        func_call = self._contract.functions.transfer(to, value)
        return self.__wallet.send_transaction(func_call)

    def transfer_from(self, from_addr: str, to: str, value: int) -> str:
        """
        Transfers CELO from one address to another on behalf of a user

        Parameters:
            from_addr: str
                The address to transfer CELO from
            to: str
                The address to transfer CELO to
            value: int
                The amount of CELO to transfer
        Returns:
            Transaction hash
        """
        func_call = self._contract.functions.transferFrom(from_addr, to, value)
        return self.__wallet.send_transaction(func_call)

    def balance_of(self, addr: str) -> int:
        """
        Gets the balance of the specified address

        Parameters:
            addr: str
                The address to query the balance of
        Returns:
            int
        """
        return self.web3.eth.getBalance(addr)
