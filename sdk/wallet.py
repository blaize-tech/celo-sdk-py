import ast
import sys

import web3
from eth_account import Account
from eth_account.datastructures import SignedTransaction
from hexbytes import HexBytes
from web3 import Web3


class Wallet:
    """
    Wallet requires for transaction building, signing and sending to the blockchain

    Attributes
        web3: web3.Web3
            web3 object
        priv_key: bytes
            private key in bytes (b'')
    """

    def __init__(self, web3: Web3, priv_key: bytes, gas_price_contract: "GasPriceContractWrapper"):
        self.web3 = web3
        acc = Account()
        self._account = acc.from_key(priv_key)
        self.gas_price_contract = gas_price_contract
        self.address = self._account.address
        self.fee_currency = None
        self.gateway_fee_recipient = None
        self.gateway_fee = None
        self.gas = 10000000
        self.gas_increase_step = 1000000

    @property
    def fee_currency(self):
        return self.fee_currency
    
    @property
    def gateway_fee_recipient(self):
        return self.gateway_fee_recipient

    @property
    def gateway_fee(self):
        return self.gateway_fee

    @fee_currency.setter
    def fee_currency(self, new_fee_currency: str):
        if self.web3.isAddress(new_fee_currency):
            self.fee_currency = new_fee_currency
        else:
            raise TypeError("Incorrect fee currency address")

    @gateway_fee_recipient.setter
    def gateway_fee_recipient(self, new_gateway_fee_recipient: str):
        if self.web3.is_Address(new_gateway_fee_recipient):
            self.gateway_fee_recipient = new_gateway_fee_recipient
        else:
            raise TypeError("Incorrect gateway fee recipient")

    @gateway_fee.setter
    def gateway_fee(self, new_gateway_fee: int):
        if type(new_gateway_fee) == int:
            self.gateway_fee = new_gateway_fee
        else:
            raise TypeError("Incorrect new gateway fee type data")

    def construct_transaction(self, contract_method: web3._utils.datatypes, gas: int = None) -> dict:
        """
        Takes contract method call object and builds transaction dict with it

        Parameters:
            contract_method: web3._utils.datatypes
        Returns:
            constructed transaction in dict
        """
        try:
            nonce = self.web3.eth.getTransactionCount(self.address)

            if self.fee_currency:
                gas = gas if gas else self.gas
                base_rows = {'gasPrice': self.get_gas_price(
                ), 'nonce': nonce, 'gas': gas, 'from': self.address, 'feeCurrency': self.fee_currency}
            else:
                raise ValueError(
                    "Can't construct transaction without fee currency, set fee currency please")

            if self.gateway_fee_recipient:
                base_rows['gatewayFeeRecipient'] = self.gateway_fee_recipient

            if self.gateway_fee:
                base_rows['gatewayFee'] = self.gateway_fee

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
            signed_tx = self._account.sign_transaction(tx)
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
                gas = gas + self.gas_increase_step if gas else self.gas + self.gas_increase_step
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

    def get_gas_price(self) -> int:
        try:
            gas_price = self.gas_price_contract.functions.gasPriceMinimum().call()  # TODO: change here to call ContractWrapper function
            return gas_price
        except:
            raise Exception(
                f"Error while contract method to get gas price: {sys.exc_info()[1]}")
