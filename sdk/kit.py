import sys

from sdk.wallet import Wallet
from sdk.contracts.base_wrapper import BaseWrapper

from web3 import Web3


class Kit:
    def __init__(self, provider_url: str, wallet: Wallet = None):
        if provider_url.find(".ipc") == len(provider_url) - 4:
            self.provider = Web3.IPCProvider(provider_url)
        elif provider_url.startswith("ws://"):
            self.provider = Web3.WebsocketProvider(provider_url)
        else:
            self.provider = Web3.HTTPProvider(provider_url)
        self.__wallet = wallet

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
