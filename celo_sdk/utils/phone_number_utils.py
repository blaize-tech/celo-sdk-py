import re


identifier_type = {
    'phone_number': 0
}

PHONE_SALT_SEPARATOR = '__'
E164_REGEX = '^\+[1-9][0-9]{1,14}$'

def get_identifier_prefix(data_type: str):
    try:
        return identifier_type[data_type]
    except:
        raise Exception('There is no such an identifier')

def get_phone_hash(sha3_function: 'SHA3 web3 function object', phone_number: str, salt: str = None):
    if not bool(re.match(E164_REGEX, phone_number)):
        raise Exception(f"Attempting to hash a non-e164 number: {phone_number}")
    
    prefix = str(get_identifier_prefix('phone_number'))
    value = prefix + phone_number if salt == None else prefix + (phone_number + PHONE_SALT_SEPARATOR + salt)

    return sha3_function(['string'], [value]).hex()