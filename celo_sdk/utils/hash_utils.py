from web3 import Web3
import string

def is_message_hex_strict(message:str) -> bool:
    if message[:2] == '0x':
        for letter in message:
            if letter not in string.hexdigits:
                return False
        return True
    else:
        return False

def message_length(message: str) -> str:
    if is_message_hex_strict(message):
        return str(len(message - 2) / 2)
    else:
        return str(len(message))

def hash_message_with_prefix(web3: Web3, message: str) -> str:
    prefix = '\x19Ethereum Signed Message:\n'
    hashed_message = web3.soliditySha3(['string'], [prefix + message_length(message) + message])
    return hashed_message

def is_leading_with_0x(entity: str) -> str:
    if entity[:2] == '0x':
        return entity
    else:
        return '0x' + entity