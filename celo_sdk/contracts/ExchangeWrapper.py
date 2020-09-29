import sys

from celo_sdk.contracts.base_wrapper import BaseWrapper
from celo_sdk.registry import Registry

from web3 import Web3


class Exchange(BaseWrapper):
    """
    Contract that allows to exchange StableToken for GoldToken and vice versa
    using a Constant Product Market Maker Model

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
    
    def spread(self) -> int:
        """
        Query spread parameter

        Returns:
            int
                Current spread charged on exchanges
        """
        return self._contract.functions.spread().call()
    
    def reserve_fraction(self) -> int:
        """
        Query reserve fraction parameter

        Returns:
            int
                Current fraction to commit to the gold bucket
        """
        return self._contract.functions.reserveFraction().call()
    
    def update_frequency(self) -> int:
        """
        Query update frequency parameter

        Returns:
            int
                The time period that needs to elapse between bucket
                updates
        """
        return self._contract.functions.updateFrequency().call()
    
    def minimum_reports(self) -> int:
        """
        Query minimum reports parameter

        Returns:
            int
                The minimum number of fresh reports that need to be
                present in the oracle to update buckets
                commit to the gold bucket
        """
        return self._contract.functions.minimumReports().call()
    
    def last_bucket_update(self) -> int:
        """
        Query last bucket update

        Returns:
            int
                The timestamp of the last time exchange buckets were updated.
        """
        return self._contract.functions.lastBucketUpdate().call()
    
    def get_buy_token_amount(self, sell_amount: int, sell_gold: bool) -> int:
        """
        Returns the amount of buyToken a user would get for sellAmount of sellToken

        Prameters:
            sell_amount: int
                The amount of sellToken the user is selling to the exchange
            sell_gold: bool
                `true` if gold is the sell token
        Returns:
            bool
                The corresponding buyToken amount
        """
        if sell_amount == 0:
            return 0
        
        return self._contract.functions.getBuyTokenAmount(sell_amount, sell_gold).call()
    
    def get_sell_token_amount(self, buy_amount: int, sell_gold: bool) -> int:
        """
        Returns the amount of sellToken a user would need to exchange to receive buyAmount of
        buyToken

        Parameters:
            buy_amount: int
                The amount of buyToken the user would like to purchase
            sell_gold: bool
                `true` if gold is the sell token
        Returns:
            int
                The corresponding sellToken amount
        """
        if buy_amount == 0:
            return 0
        
        return self._contract.functions.getSellTokenAmount(buy_amount, sell_gold).call()
    
    def get_buy_and_sell_buckets(self, sell_gold: bool) -> list:
        """
        Returns the buy token and sell token bucket sizes, in order. The ratio of
        the two also represents the exchange rate between the two.

        Parameters:
            sell_gold: bool
                `true` if gold is the sell token
        Returns: list
        """
        return self._contract.functions.getBuyAndSellBuckets(sell_gold).call()
    
    def exchange(self, sell_amount: int, min_buy_amount: int, sell_gold: bool) -> str:
        """
        Exchanges sellAmount of sellToken in exchange for at least minBuyAmount of buyToken
        Requires the sellAmount to have been approved to the exchange

        Parameters:
            sell_amount: int
                The amount of sellToken the user is selling to the exchange
            min_buy_amount: int
                The minimum amount of buyToken the user has to receive for this
                transaction to succeed
            sell_gold: bool
                `true` if gold is the sell token
        Returns:
            str
                Transaction hash
        """
        func_call = self._contract.functions.exchange(sell_amount, min_buy_amount, sell_gold)
        
        return self.__wallet.send_transaction(func_call)
    
    def sell_gold(self, amount: int, min_usd_amount: int) -> str:
        """
        Exchanges amount of CELO in exchange for at least minUsdAmount of cUsd
        Requires the amount to have been approved to the exchange

        Parameters:
            amount: int
                The amount of CELO the user is selling to the exchange
            min_usd_amount: int
                The minimum amount of cUsd the user has to receive for this
                transaction to succeed
        Returns:
            str
                Transaction hash
        """
        return self.exchange(amount, min_usd_amount, True)

    def sell_dollar(self, amount: int, min_gold_amount: int) -> str:
        """
        Exchanges amount of cUsd in exchange for at least minGoldAmount of CELO
        Requires the amount to have been approved to the exchange

        Parameters:
            amount: int
                The amount of cUsd the user is selling to the exchange
            min_gold_amount: int
                The minimum amount of CELO the user has to receive for this
                transaction to succeed
        Returns:
            str
                Transaction hash
        """
        return self.exchange(amount, min_gold_amount, False)
    
    def quote_usd_sell(self, sell_amount: int) -> int:
        """
        Returns the amount of CELO a user would get for sellAmount of cUsd

        Parameters:
            sell_amount: int
                The amount of cUsd the user is selling to the exchange
        Returns:
            int
                The corresponding CELO amount
        """
        return self.get_buy_token_amount(sell_amount, False)
    
    def quote_gold_sell(self, sell_amount: int) -> int:
        """
        Returns the amount of cUsd a user would get for sellAmount of CELO

        Parameters:
            sell_amount: int
                The amount of CELO the user is selling to the exchange
        Returns:
            int
                The corresponding cUsd amount
        """
        return self.get_buy_token_amount(sell_amount, True)
    
    def quote_usd_buy(self, buy_amount: int) -> int:
        """
        Returns the amount of CELO a user would need to exchange to receive buyAmount of
        cUsd

        Parameters:
            buy_amount: int
                The amount of cUsd the user would like to purchase
        Returns:
            int
                The corresponding CELO amount
        """
        return self.get_sell_token_amount(buy_amount, False)
    
    def quote_gold_buy(self, buy_amount: int) -> int:
        """
        Returns the amount of cUsd a user would need to exchange to receive buyAmount of
        CELO

        Parameters:
            buy_amount: int
                The amount of CELO the user would like to purchase
        Returns:
            int
                The corresponding cUsd amount
        """
        return self.get_sell_token_amount(buy_amount, True)
    
    def get_config(self) -> dict:
        """
        Returns the current configuration of the exchange contract
        """
        spread = self.spread()
        reserve_fraction = self.reserve_fraction()
        update_frequency = self.update_frequency()
        minimum_reports = self.minimum_reports()
        last_bucket_update = self.last_bucket_update()

        return {
            'spread': spread,
            'reserve_fraction': reserve_fraction,
            'update_frequency': update_frequency,
            'minimum_reports': minimum_reports,
            'last_bucket_update': last_bucket_update
        }
    
    def get_exchange_rate(self, buy_amount: int, sell_gold: bool) -> float:
        """
        Returns the exchange rate estimated at buyAmount

        Parameters:
            buy_amount: int
                The amount of buyToken in wei to estimate the exchange rate at
            sell_gold: bool
                `true` if gold is the sell token
        Returns:
            float
                The exchange rate (number of sellTokens received for one buyToken)
        """
        taker_amount = self.get_buy_token_amount(buy_amount, sell_gold)

        return buy_amount / taker_amount
    
    def get_usd_exchange_rate(self, buy_amount: int) -> float:
        """
        Returns the exchange rate for cUsd estimated at the buyAmount

        Parameters:
            buy_amount: int
                The amount of cUsd in wei to estimate the exchange rate at
        Returns:
            float
                The exchange rate (number of CELO received for one cUsd)
        """
        return self.get_exchange_rate(buy_amount, False)

    def get_gold_exchange_rate(self, buy_amount: int) -> float:
        """
        Returns the exchange rate for CELO estimated at the buyAmount

        Parameters:
            buy_amount: int
                The amount of CELO in wei to estimate the exchange rate at
        Returns:
            float
                The exchange rate (number of CELO received for one cUsd)
        """
        return self.get_exchange_rate(buy_amount, True)
