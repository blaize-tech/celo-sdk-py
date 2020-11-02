import sys
from importlib import import_module

from celo_sdk.contracts.GasPriceMinimumWrapper import GasPriceMinimum
from celo_sdk.registry import Registry
from celo_sdk.wallet import Wallet

from web3 import Web3


class BaseWrapper:
    def __init__(self, web3: Web3, registry: Registry, wallet: Wallet = None):
        self.web3 = web3
        self.registry = registry
        if not self.registry.registry:
            self.registry.set_registry()
        self.wallet = wallet
        self.contracts = {}
        self.null_address = '0x0000000000000000000000000000000000000000'

    @classmethod
    def get_gas_price_contract(self, w3: Web3, registry: Registry):
        try:
            gas_contract_data = registry.load_contract_by_name('GasPriceMinimum')
            contract = GasPriceMinimum(w3, gas_contract_data['address'], gas_contract_data['abi'])
            return contract
        except:
            raise Exception(f"Error while create GasPriceMinimum wrapper contract:\n{sys.exc_info()[1]}")

    def create_all_the_contracts(self):
        """
        Creates objects of all the contracts and saves it to the dictionary
        """
        try:
            contracts_data_list = self.registry.load_all_contracts()
            for contract_data in contracts_data_list:
                self.create_contract(
                    contract_data['contract_name'], contract_data['address'], contract_data['abi'])
        except:
            raise Exception(
                f"Error occurs while create all the contracts objecst:\n{sys.exc_info()[1]}")

    def create_and_get_contract_by_name(self, contract_name: str, contract_address: str = None) -> 'ContractWrapperObject':
        self.create_contract_by_name(contract_name, contract_address)
        return self.get_contract_by_name(contract_name)

    def get_contract_by_name(self, contract_name: str) -> 'ContractWrapperObject':
        """
        Returns contract wrapper object if it was created and raises exception if was not

        Parameters:
            contract_name: str
        Returns:
            contract wrapper object
        """
        contract_obj = self.contracts.get(contract_name)
        if not contract_obj:
            raise KeyError(
                "Such a contract was not created yet, call create_contract_by_name() or create_all_the_contracts() first")
        return contract_obj

    def create_contract_by_name(self, contract_name: str, contract_address: str = None):
        """
        Creates contract wrapper object by contract name and saves to the dictionary

        Parameters:
            contract_name: str
        """
        contract_obj = self.contracts.get(contract_name)
        if contract_obj:
            return
        contract_data = self.registry.load_contract_by_name(contract_name, contract_address)

        self.create_contract(
            contract_name, contract_data['address'], contract_data['abi'])

    def create_contract(self, contract_name: str, contract_address: str, abi: list):
        """
        Creates contract wrapper object by contract data and saves it to the dictionary
        """
        try:
            contract_obj = self.contracts.get(contract_name)
            if contract_obj:
                raise Exception("Such a contract already created")
            contract_module = import_module(
                f"celo_sdk.contracts.{contract_name}Wrapper")
            contract_obj = getattr(contract_module, contract_name)
            contract = contract_obj(
                web3=self.web3, registry=self.registry, address=contract_address, abi=abi, wallet=self.wallet)

            self.contracts[contract_name] = contract
        except ModuleNotFoundError:
            raise ModuleNotFoundError(
                "Can't find smart contract wrapper in contracts/ directory")
        except:
            raise Exception(
                f"Error occurs while create contract object:\n{sys.exc_info()[1]}")
