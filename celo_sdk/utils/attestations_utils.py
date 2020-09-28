import requests
import json
from web3 import Web3
from celo_sdk.celo_account.account import Account


DEFAULT_NUM_ATTESTATIONS_REQUIRED = 3
DEFAULT_ATTESTATION_THRESHOLD = 0.25

CLAIM_TYPES = {
    'attestation_service_url': 'ATTESTATION_SERVICE_URL',
    'account': 'ACCOUNT',
    'domain': 'DOMAIN',
    'keybase': 'KEYBASE',
    'name': 'NAME',
    'profile_picture': 'PROFILE_PICTURE',
    'storage': 'STORAGE',
    'twitter': 'TWITTER'
}

SINGULAR_CLAIM_TYPES = [CLAIM_TYPES['name'], CLAIM_TYPES['attestation_service_url']]


def is_account_considered_verified(stats: 'AttestationStat', num_attestations_required: int, attestation_threshold: float) -> dict:
    num_attestations_required = num_attestations_required if num_attestations_required else DEFAULT_NUM_ATTESTATIONS_REQUIRED
    attestation_threshold = attestation_threshold if attestation_threshold else DEFAULT_ATTESTATION_THRESHOLD

    num_attestations_remaining = num_attestations_required - stats['completed']
    fraction_attestation = 0 if stats['total'] < 1 else stats['completed'] / stats['total']
    is_verified = num_attestations_remaining <= 0 and fraction_attestation >= attestation_threshold

    return {
        'is_verified': is_verified,
        'num_attestations_remaining': num_attestations_remaining,
        'total': stats['total'],
        'completed': stats['completed']
    }

def parse_solidity_string_array(string_lengths: list, data: str) -> list:
    if data == None:
        data = '0x'
    
    ret = []
    offset = 0

    raw_data = bytes.fromhex(data.lstrip('0x'))
    print(raw_data)
    for i, _ in enumerate(string_lengths):
        string = raw_data[offset : offset + string_lengths[i]].decode("ASCII")
        offset += string_lengths[i]
        ret.append(string)
    
    return ret

def zip3(a: list, b: list, c: list) -> list:
    length = min(len(a), len(b), len(c))
    res = []

    for el in range(length):
        res.append([a[el], b[el], c[el]])
    
    return res

# TODO: test this method with real data
def fetch_from_url(w3: 'Web3', url: str) -> dict:
    resp = requests.get(url)
    if resp.status_code != 200:
        raise Exception(f"Request failed with status: {resp.status_code}")
    return from_raw_string(w3, resp.json())

# TODO: test this method with real data, also test signature verification
def from_raw_string(w3: 'Web3', raw_data: dict) -> dict:
    claims = raw_data['claims']
    claims_hash = hash_of_claims(w3, claims)

    signer_address = Account.recoverHash(claims_hash, signature=raw_data['meta']['signature'])
    if signer_address != raw_data['meta']['address'] and len(claims) > 0:
        raise Exception("Signature could not be validated")
    
    for claim_type in SINGULAR_CLAIM_TYPES:
        claims = [el for el in raw_data['claims'] if el['type'] == claim_type]
        if len(claims) > 1:
            raise Exception(f"Found {len(claims)} claims of type {claim_type}, should be at most 1")

    return raw_data

def hash_of_claims(w3: 'Web3', claims: list):
    return list(map(lambda claim: w3.soliditySha3(['string'], [json.dumps(claim)]).hex(), claims))[0]
