import ast
import sys

import web3
from eth_account import Account
from eth_account.datastructures import SignedTransaction
from hexbytes import HexBytes
from web3 import Web3


class Wallet:
    """
    Wallet class requires for transaction building, signing and sending to the blockchain.
    Also you can configure Wallet as you wish by using settres methods

    Attributes
        web3: web3.Web3
            web3 object
        priv_key: bytes
            private key in bytes (b'')
        gas_price_contract: sdk.contracts.GasPriceMinimum (optional)
            GasPriceMinimum contract wrapper
    """

    def __init__(self, web3: Web3, priv_key: bytes, gas_price_contract: "GasPriceContractWrapper" = None):
        self.web3 = web3
        self.__accounts = {}
        acc = Account()
        self.active_account = acc.from_key(priv_key)
        self.__accounts.update({self.active_account.address: self.active_account})
        self.gas_price_contract = gas_price_contract
        self._fee_currency = None  # TODO: by default set to Celo token ?
        self._gateway_fee_recipient = None
        self._gateway_fee = None
        self._gas_price = None
        self._gas = 10000000
        self.gas_increase_step = 1000000

    @property
    def fee_currency(self) -> str:
        return self._fee_currency

    @property
    def gateway_fee_recipient(self) -> str:
        return self._gateway_fee_recipient

    @property
    def gateway_fee(self) -> int:
        return self._gateway_fee

    @property
    def gas_price(self) -> int:
        return self._gas_price

    @property
    def gas(self) -> int:
        return self._gas

    @property
    def accounts(self) -> dict:
        return self.__accounts

    @gas_price.setter
    def gas_price(self, new_gas_price: int):
        if type(new_gas_price) != int:
            raise TypeError("Gas price value should be int type")
        self._gas_price = new_gas_price

    @fee_currency.setter
    def fee_currency(self, new_fee_currency: str):
        if not self.web3.isAddress(new_fee_currency):
            raise TypeError("Incorrect fee currency address")
        self._fee_currency = new_fee_currency

    @gateway_fee_recipient.setter
    def gateway_fee_recipient(self, new_gateway_fee_recipient: str):
        if not self.web3.is_Address(new_gateway_fee_recipient):
            raise TypeError("Incorrect gateway fee recipient")
        self._gateway_fee_recipient = new_gateway_fee_recipient

    @gateway_fee.setter
    def gateway_fee(self, new_gateway_fee: int):
        if type(new_gateway_fee) != int:
            raise TypeError("Incorrect new gateway fee type data")
        self._gateway_fee = new_gateway_fee

    @gas.setter
    def gas(self, new_gas: int):
        if type(new_gas) != int:
            raise TypeError("Incorrect new gas type data")
        self._gas = new_gas

    @accounts.setter
    def accounts(self, new_acc: Account):
        if type(new_acc) != Account:
            raise TypeError("Incorrect new account type")
        self.__accounts.update({new_acc.address: new_acc})
        self.active_account = new_acc

    def add_new_key(self, priv_key: bytes):
        acc = Account()
        self.active_account = acc.from_key(priv_key)
        self.__accounts.update({self.active_account.address: self.active_account})

    def remove_account(self, account_address: str):
        del self.__accounts[account_address]

    def change_account(self, account_address: str):
        if account_address not in self.__accounts:
            raise KeyError("There is no account with such an address in wallet")
        self.active_account = self.__accounts[account_address]

    def construct_transaction(self, contract_method: web3._utils.datatypes, gas: int = None) -> dict:
        """
        Takes contract method call object and builds transaction dict with it

        Parameters:
            contract_method: web3._utils.datatypes
            gas: int (optional)
        Returns:
            constructed transaction in dict
        """
        try:
            nonce = self.web3.eth.getTransactionCount(self.active_account.address)

            if self._fee_currency:
                gas = gas if gas else self._gas
                gas_price = self._gas_price if self._gas_price else self.get_network_gas_price()
                base_rows = {'gasPrice': gas_price, 'nonce': nonce, 'gas': gas,
                             'from': self.active_account.address, 'feeCurrency': self._fee_currency}
            else:
                raise ValueError(
                    "Can't construct transaction without fee currency, set fee currency please")

            if self._gateway_fee_recipient:
                base_rows['gatewayFeeRecipient'] = self._gateway_fee_recipient

            if self._gateway_fee:
                base_rows['gatewayFee'] = self._gateway_fee

            tx = contract_method.buildTransaction(base_rows)
            return tx
        except:
            raise Exception(
                f"Error while construct transaction: {sys.exc_info()[1]}")

    def sign_transaction(self, tx: dict) -> SignedTransaction:
        """
        Takes transaction dict, signs it and sends to the blockchain

        Parameters:
            tx: dict
                transaction data in dict
        Returns:
            signed transaction object
        """
        try:
            signed_tx = self.active_account.sign_transaction(tx)
            return signed_tx
        except:
            raise Exception(
                f"Error while sign transaction: {sys.exc_info()[1]}")

    def construct_and_sign_transaction(self, contract_method: web3._utils.datatypes) -> SignedTransaction:
        """
        Takes contract method call object, call method to build transaction and return signed transaction

        Parameters:
            contract_method: web3._utils.datatypes
                object of contract method call
        Returns:
            signed transaction object
        """
        try:
            tx = self.construct_transaction(contract_method)
            signed_tx = self.sign_transaction(tx)
            return signed_tx
        except:
            raise Exception(
                f"Error while sign transaction: {sys.exc_info()[1]}")

    def send_transaction(self, contract_method: web3._utils.datatypes, gas: int = None) -> str:
        """
        Takes contract method call object, call method to build transaction and push it to the blockchain

        Parameters:
            contract_method: web3._utils.datatypes
                object of contract method call
            gas: int (optional)
        Returns:
            hash of sended transaction
        """
        try:
            tx = self.construct_transaction(contract_method, gas=gas)
            signed_tx = self.sign_transaction(tx)
            return self.push_tx_to_blockchain(signed_tx.rawTransaction)
        except ValueError as e:
            error_message = ast.literal_eval(str(e))['message']
            if error_message == 'intrinsic gas too low':
                print(
                    "Got error about too low gas value. Increase gas value and try to send it again.")
                gas = gas + self.gas_increase_step if gas else self._gas + self.gas_increase_step
                self.send_transaction(contract_method, gas)
            else:
                raise ValueError(error_message)
        except:
            raise Exception(
                f"Error while send transaction: {sys.exc_info()[1]}")

    def push_tx_to_blockchain(self, signed_raw_tx: HexBytes) -> str:
        """
        Takes signed raw transaction in HexBytes and push it to the blockchain

        Parameters:
            signed_raw_tx: HexBytes
                raw signed transaction
        Returns:
            hash of sent transaction
        """
        tx_hash = self.web3.eth.sendRawTransaction(signed_raw_tx)
        return tx_hash.hex()

    def get_network_gas_price(self) -> int:
        """
        Calls smart contract method to get network gas price

        Returns:
            gas price
        """
        try:
            if not self.gas_price_contract:
                raise ValueError(
                    "Set GasPriceMinimum wrapper to the wallet to get network gas price")
            # TODO: change here to call ContractWrapper function
            gas_price = self.gas_price_contract.functions.gasPriceMinimum().call()
            return gas_price
        except:
            raise Exception(
                f"Error while contract method to get gas price: {sys.exc_info()[1]}")
