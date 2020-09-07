import sys

from web3 import Web3
from web3.auto import w3

from sdk.contracts.base_wrapper import BaseWrapper
from sdk.registry import Registry
from sdk.wallet import Wallet


class Kit:
    """
    Main class through which all the functionality is accessible.
    With this class you can configure Wallet parameters, set new keys for the wallet, get totall address balance and network configs.

    Attributes:
        provider_url: str
            url address of Celo node
        wallet: Wallet (optional)
    """
    def __init__(self, provider_url: str, wallet: Wallet = None):
        if provider_url.find(".ipc") == len(provider_url) - 4:
            provider = Web3.IPCProvider(provider_url)
        elif provider_url.startswith("ws://"):
            provider = Web3.WebsocketProvider(provider_url)
        else:
            provider = Web3.HTTPProvider(provider_url)
        self.w3 = Web3(provider)
        registry = Registry(self.w3)
        registry.set_registry()
        gas_price_contract = BaseWrapper.get_gas_price_contract(self.w3, registry)
        self.__wallet = self.create_wallet(gas_price_contract)
        self.base_wrapper = BaseWrapper(self.w3, registry, self.__wallet)
        self.__wallet.fee_currency = self.base_wrapper.registry.load_contract_by_name("StableToken")['address']

    @property
    def wallet(self):
        return self.__wallet

    @wallet.setter
    def wallet(self, wallet: Wallet):
        if type(wallet) == Wallet:
            self.__wallet = wallet
        else:
            raise Exception("Only Wallet object can be set to the Kit")

    @wallet.setter
    def wallet_fee_currency(self, fee_currency: str):
        self.__wallet.fee_currency = fee_currency

    @wallet.setter
    def wallet_gateway_fee_recipient(self, gateway_fee_recipient: str):
        self.__wallet.gateway_fee_recipient = gateway_fee_recipient

    @wallet.setter
    def wallet_gateway_fee(self, gateway_fee: int):
        self.__wallet.gateway_fee = gateway_fee

    @wallet.setter
    def wallet_gas_price(self, gas_price: int):
        self.__wallet.gas_price = gas_price

    @wallet.setter
    def wallet_gas(self, gas: int):
        self.__wallet.gas = gas

    @wallet.setter
    def wallet_add_new_key(self, priv_key: bytes):
        self.__wallet.add_new_key(priv_key)

    @wallet.setter
    def wallet_change_account(self, account_address: str):
        self.__wallet.change_account(account_address)

    def create_wallet(self, registry: Registry, priv_key: bytes = None):
        if not priv_key:
            priv_key = self.generate_new_key()
        wallet = Wallet(self.w3, priv_key, registry)
        return wallet

    def generate_new_key(self):
        acct = w3.eth.account.create()
        return acct.privateKey

    def get_total_balance(self):
        pass

    def get_network_config(self):
        pass
