from celo_sdk.contracts.base_wrapper import BaseWrapper
from celo_sdk.registry import Registry

from web3 import Web3


class StableToken(BaseWrapper):
    """
    Class which wrapp all the methods of StableToken smart contract

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

    def allowance(self, account_owner: str, spender: str) -> int:
        """
        Gets the amount of owner's StableToken allowed to be spent by spender

        Parameters:
            account_owner: str
                The owner of the StableToken
            spender: str
                The spender of the StableToken
        Returns:
            The amount of StableToken owner is allowing spender to spend
        """
        return self._contract.functions.allowance(account_owner, spender).call()

    def name(self) -> str:
        """
        Returns name of token

        Returns:
            str
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

    def balance_of(self, address: str) -> int:
        """
        Returns balance of address

        Parameters:
            address: str
        Returns:
            int
        """
        return self._contract.functions.balanceOf(address).call()

    def owner(self) -> str:
        """
        Returns owner of smart contract

        Returns:
            str
        """
        return self._contract.functions.owner().call()

    def value_to_units(self, value: int) -> int:
        """
        Converts value to units

        Parameters:
            value: int
        Returns:
            int
        """
        return self._contract.functions.valueToUnits(value).call()

    def units_to_value(self, units: int) -> int:
        """
        Converts units to value

        Parameters:
            units: int
        Returns:
            int
        """
        return self._contract.functions.unitsToValue(units).call()

    def increase_allowance(self, spender: str, value: int) -> str:
        """
        Increases the allowance of another user

        Parameters:
            spender: str
                The address which is being approved to spend StableToken
            value: int
                The increment of the amount of StableToken approved to the spender
        Returns:
            Transaction hash
        """
        func_call = self._contract.functions.increaseAllowance(spender, value)
        return self.__wallet.send_transaction(func_call)

    def decrease_allowance(self, spender: str, value: int) -> str:
        """
        Decrease the allowance of another user

        Parameters:
            spender: str
                The address which is being approved to spend StableToken
            value: int
                The decrease of the amount of StableToken approved to the spender
        Returns:
            Transaction hash
        """
        func_call = self._contract.functions.decreaseAllowance(spender, value)
        return self.__wallet.send_transaction(func_call)

    def set_inflation_parameters(self):
        func_call = self._contract.functions.setInflationParameters()
        return self.__wallet.send_transaction(func_call)

    def get_inflation_parameters(self) -> dict:
        """
        Querying the inflation parameters

        Returns:
            dict
        """
        inflation_params = self._contract.functions.getInflationParameters().call()
        return {
            'rate': inflation_params[0],
            'factor': inflation_params[1],
            'updatePeriod': inflation_params[2],
            'factorLastUpdated': inflation_params[3]
        }

    def get_config(self) -> dict:
        """
        Returns current configuration parameters

        Returns:
            dict
        """
        name = self.name()
        symbol = self.symbol()
        decimals = self.decimals()
        inflation_params = self.get_inflation_parameters()
        return {
            'name': name,
            'symbol': symbol,
            'decimals': decimals,
            'inflation_parameters': inflation_params
        }

    def approve(self, spender: str, value: str) -> str:
        """
        Approve a user to transfer StableToken on behalf of another user

        Parameters:
            spender: str
                The address which is being approved to spend StableToken
            value: str
                The amount of StableToken approved to the spender
        Returns:
            Transaction hash
        """
        func_call = self._contract.functions.approve(spender, value)
        return self.__wallet.send_transaction(func_call)

    def transfer_with_comment(self, to: str, value: int, comment: str) -> str:
        """
        Transfer token for a specified address

        Parameters:
            to: str
                The address to transfer to
            value: int
                The amount to be transferred
            comment: str
                The transfer comment
        Returns:
            Transaction hash
        """
        func_call = self._contract.functions.transferWithComment(to, value, comment)
        return self.__wallet.send_transaction(func_call)
    
    def transfer(self, to: str, value: int) -> str:
        """
        Transfer value to pointed address

        Parameters:
            to: str
                The address to transfer to
            value: int
                The amount to be transferred
        Returns:
            Transaction hash
        """
        func_call = self._contract.functions.transfer(to, value)
        return self.__wallet.send_transaction(func_call)

    def transfer_from(self, from_addr: str, to: str, value: int) -> str:
        """
        Transfers StableToken from one address to another on behalf of a user

        Parameters:
            from_addr: str
                The address to transfer StableToken from
            to: str
                The address to transfer StableToken to
            value: str
                The amount of StableToken to transfer
        Returns:
            Transaction hash
        """
        func_call = self._contract.functions.transferFrom(from_addr, to, value)
        return self.__wallet.send_transaction(func_call)