from typing import List

from web3 import Web3

from celo_sdk.contracts.base_wrapper import BaseWrapper
from celo_sdk.registry import Registry


class Reserve(BaseWrapper):
    """
    Contract for handling reserve for stable currencies

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
    
    def tobin_tax_staleness_threshold(self) -> int:
        """
        Query Tobin tax staleness threshold parameter

        Returns:
            int
                Current Tobin tax staleness threshold
        """
        return self._contract.functions.tobinTaxStalenessThreshold().call()
    
    def is_spender(self, account: str) -> bool:
        return self._contract.functions.isSpender(account).call()
    
    def transfer_gold(self, to_addrs: str, value: int) -> str:
        func_call = self._contract.functions.transferGold(to_addrs, value)

        return self.__wallet.send_transaction(func_call)
    
    def get_or_compute_tobin_tax(self) -> List[int]:
        return self._contract.functions.getOrComputeTobinTax().call()
    
    def frozen_reserve_gold_start_balance(self) -> int:
        return self._contract.functions.frozenReserveGoldStartBalance().call()
    
    def frozen_reserve_gold_start_day(self) -> int:
        return self._contract.functions.frozenReserveGoldStartDay().call()
    
    def frozen_reserve_gold_days(self) -> int:
        return self._contract.functions.frozenReserveGoldDays().call()
    
    def get_reserve_gold_balance(self) -> int:
        return self._contract.functions.getReserveGoldBalance().call()
    
    def get_other_reserve_addresses(self) -> List[str]:
        return self._contract.functions.getOtherReserveAddresses().call()
    
    def get_config(self) -> dict:
        """
        Returns current configuration parameters
        """
        tobin_tax_staleness_threshold = self.tobin_tax_staleness_threshold()
        frozen_reserve_gold_start_balance = self.frozen_reserve_gold_start_balance()
        frozen_reserve_gold_start_day = self.frozen_reserve_gold_start_day()
        frozen_reserve_gold_days = self.frozen_reserve_gold_days()
        other_reserve_addresses = self.get_other_reserve_addresses()

        return {
            'tobin_tax_staleness_threshold': tobin_tax_staleness_threshold,
            'frozen_reserve_gold_start_balance': frozen_reserve_gold_start_balance,
            'frozen_reserve_gold_start_day': frozen_reserve_gold_start_day,
            'frozen_reserve_gold_days': frozen_reserve_gold_days,
            'other_reserve_addresses': other_reserve_addresses
        }
    
    def is_other_reserve_addresses(self, address: str) -> bool:
        return self._contract.functions.isOtherReserveAddress(address).call()
    
    def get_spenders(self) -> List[str]:
        spenders_added = self._contract.events.SpenderAdded.getLogs(fromBlock=0, toBlock='latest')
        spenders_added = [spender['args']['spender'] for spender in spenders_added]

        spenders_removed = self._contract.events.SpenderRemoved.getLogs(fromBlock=0, toBlock='latest')
        spenders_removed = [spender['args']['spender'] for spender in spenders_removed]

        return [addr for addr in spenders_added if addr not in spenders_removed]
