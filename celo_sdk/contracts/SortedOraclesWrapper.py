from typing import List

from celo_sdk.contracts.base_wrapper import BaseWrapper
from celo_sdk.registry import Registry

from web3 import Web3


class SortedOracles(BaseWrapper):
    """
    Currency price oracle contract

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
    
    def num_rates(self, token: str) -> int:
        """
        Gets the number of rates that have been reported for the given token

        Parameters:
            token: str
                The CeloToken token for which the CELO exchange rate is being reported
                "GoldToken" or "StableToken"
        Returns:
            int
                The number of reported oracle rates for `token`
        """
        token_address = self.registry.registry.functions.getAddressForString(token).call()
        
        return self._contract.functions.numRates(token_address).call()
    
    def median_rate(self, token: str) -> dict:
        """
        Returns the median rate for the given token

        Parameters:
            token: str
                The CeloToken token for which the CELO exchange rate is being reported
                "GoldToken" or "StableToken"
        Returns:
            dict
                The median exchange rate for `token`, expressed as:
                amount of that token / equivalent amount in CELO
        """
        token_address = self.registry.registry.functions.getAddressForString(token).call()
        func_call = self._contract.functions.medianRate(token_address).call()

        return {'rate': func_call[0] / func_call[1]}
    
    def is_oracle(self, token: str, oracle: str) -> bool:
        """
        Checks if the given address is whitelisted as an oracle for the token

        Parameters:
            token: str
                The CeloToken token
                "GoldToken" or "StableToken"
            oracle: str
                The address that we're checking the oracle status of
        Returns:
            bool
                boolean describing whether this account is an oracle
        """
        token_address = self.registry.registry.functions.getAddressForString(token).call()

        return self._contract.functions.isOracle(token_address, oracle).call()
    
    def get_oracles(self, token: str) -> List[str]:
        """
        Returns the list of whitelisted oracles for a given token

        Parameters:
            token: str
                The CeloToken token
                "GoldToken" or "StableToken"
        Returns:
            List[str]
                The list of whitelisted oracles for a given token
        """
        token_address = self.registry.registry.functions.getAddressForString(token).call()

        return self._contract.functions.getOracles(token_address).call()
    
    def report_expiry_seconds(self) -> int:
        """
        Returns the report expiry parameter

        Returns:
            int
                Current report expiry
        """
        return self._contract.functions.reportExpirySeconds().call()
    
    def is_oldest_report_expired(self, token: str) -> list:
        """
        Checks if the oldest report for a given token is expired

        Parameters:
            token: str
                The token for which to check reports
                "GoldToken" or "StableToken"
        Returns:
            List[bool, str]
        """
        token_address = self.registry.registry.functions.getAddressForString(token).call()

        return self._contract.functions.isOldestReportExpired(token_address).call()
    
    def remove_expired_reports(self, token: str, num_reports: int = None, parameteres: dict = None) -> str:
        """
        Removes expired reports, if any exist

        Parameters:
            token: str
                The token for which to check reports
                "GoldToken" or "StableToken"
            num_reports: int
                The upper-limit of reports to remove. For example, if there
                are 2 expired reports, and this param is 5, it will only remove the 2 that
                are expired
        Returns:
            str
                Transaction hash
        """
        token_address = self.registry.registry.functions.getAddressForString(token).call()

        if num_reports == None:
            num_reports = len(self.get_reports(token)) - 1
        
        func_call = self._contract.functions.removeExpiredReports(token_address, num_reports)

        return self.__wallet.send_transaction(func_call, parameteres)
    
    def report(self, token: str, value: int, oracle_address: str) -> str:
        """
        Updates an oracle value and the median

        Parameters:
            token: str
                The token for which the CELO exchange rate is being reported
                "GoldToken" or "StableToken"
            value: int
                The amount of `token` equal to one CELO
            oracle_address: str
        Returns:
            str
                Transaction hash
        """
        token_address = self.registry.registry.functions.getAddressForString(token).call()
        lesser_greater = self.find_lesser_and_greater_keys(token, value, oracle_address)

        func_call = self._contract.functions.report(token_address, value, lesser_greater['lesser_key'], lesser_greater['greater_key'])

        return self.__wallet.send_transaction(func_call)
    
    def report_stable_token(self, value: int, oracle_address: str) -> str:
        """
        Updates an oracle value and the median

        Parameters:
            value: int
                The amount of US Dollars equal to one CELO
            oracle_address: str
        Returns:
            str
                Transaction hash
        """
        return self.report('StableToken', value, oracle_address)
    
    def get_config(self) -> dict:
        """
        Returns current configuration parameters

        Returns:
            dict
                {'report_expiry_seconds': int}
        """
        return {'report_expiry_seconds': self.report_expiry_seconds()}
    
    def get_stable_token_rates(self) -> List[dict]:
        """
        Helper function to get the rates for StableToken, by passing the address
        of StableToken to `getRates`

        Returns:
            List[dict]
        """
        return self.get_rates('StableToken')
    
    def get_rates(self, token: str) -> List[dict]:
        """
        Gets all elements from the doubly linked list

        Parameters:
            token: str
                The CeloToken representing the token for which the Celo
                Gold exchange rate is being reported. Example: CeloContract.StableToken
        Returns:
            List[dict]
                An unpacked list of elements from largest to smallest
        """
        token_address = self.registry.registry.functions.getAddressForString(token).call()
        response = self._contract.functions.getRates(token_address).call()

        rates = []
        for ind, addr in enumerate(response[0]):
            med_rel_index = response[2][ind]
            rates.append({'address': addr, 'rate': response[1][ind], 'median_relation': med_rel_index})
        
        return rates
    
    def get_timestamps(self, token: str) -> List[dict]:
        """
        Gets all elements from the doubly linked list

        Parameters:
            token: str
                The CeloToken representing the token for which the Celo
                Gold exchange rate is being reported. Example: CeloContract.StableToken
        Returns:
            List[dict]
                An unpacked list of elements from largest to smallest
        """
        token_address = self.registry.registry.functions.getAddressForString(token).call()
        response = self._contract.functions.getTimestamps(token_address).call()
        
        timestamps = []
        for ind, addr in enumerate(response[0]):
            med_rel_index = response[2][ind]
            timestamps.append({'address': addr, 'timestamp': response[1][ind], 'median_relation': med_rel_index})
        
        return timestamps
    
    def get_reports(self, token: str) -> List[dict]:
        """
        Parameters:
            token: str
        Returns:
            List[dict]
        """
        rates = self.get_rates(token)
        timestamp = self.get_timestamps(token)

        reports = []
        for rate in rates:
            match = 0
            for t in timestamp:
                if t['address'] == rate['address']:
                    match = t['timestamp']
                    break
            reports.append({'address': rate['address'], 'rate': rate['rate'], 'timestamp': match})
        
        return reports
    
    def find_lesser_and_greater_keys(self, token: str, value: int, oracle_address: str) -> dict:
        """
        Parameters:
            token: str
            value: int
            oracle_address: str
        Returns:
            dict
        """
        current_rates = self.get_rates(token)

        greater_key = self.null_address
        lesser_key = self.null_address

        # This leverages the fact that the currentRates are already sorted from
        # greatest to lowest value
        for rate in current_rates:
            if rate['address'] != oracle_address:
                if rate['rate'] <= value:
                    lesser_key = rate['address']
                    break
                greater_key = rate['address']
        
        return {'lesser_key': lesser_key, 'greater_key': greater_key}
