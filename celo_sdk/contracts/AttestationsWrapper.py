import sys

import requests
from eth_keys.datatypes import Signature
from hexbytes import HexBytes
from web3 import Web3

from celo_sdk.celo_account._utils.signing import to_standard_signature_bytes
from celo_sdk.celo_account.account import Account
from celo_sdk.contracts.base_wrapper import BaseWrapper
from celo_sdk.registry import Registry
from celo_sdk.utils import attestations_utils
from celo_sdk.celo_account.messages import encode_defunct


class Attestations(BaseWrapper):
    """
    Attestation contract wrapper

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
        self.attestation_service_status_state = {
            'no_attestation_signer': 'NoAttestationSigner',
            'no_metadata_url': 'NoMetadataURL',
            'invalid_metadata': 'InvalidMetadata',
            'no_attestation_service_url': 'NoAttestationServiceURL',
            'unreachable_attestation_service': 'UnreachableAttestationService',
            'valid': 'Valid'
        }

    def parse_get_completable_attestations(self, response: list) -> list:
        metadata_urls = attestations_utils.parse_solidity_string_array(
            response[2], response[3])

        return [{'block_number': el[0], 'issuer': el[1], 'metadata_url': el[2]} for el in attestations_utils.zip3(response[0], response[1], metadata_urls)]

    def attestation_expiry_blocks(self) -> int:
        """
        Returns the time an attestation can be completable before it is considered expired
        """
        return self._contract.functions.attestationExpiryBlocks().call()

    def attestation_request_fees(self, address: str) -> int:
        """
        Returns the attestation request fee in a given currency

        Parameters:
            address: str
                Token address
        Returns:
            The fee as a int
        """
        return self._contract.functions.attestationRequestFees(address).call()

    def select_issuers_wait_blocks(self):
        return self._contract.functions.selectIssuersWaitBlocks().call()

    def get_unselected_request(self, identifier: str, account: str) -> dict:
        """
        Returns the unselected attestation request for an identifier/account pair, if any

        Parameters:
            identifier: str
                Attestation identifier (e.g. phone hash)
            account: str
                Address of the account
        """
        call = self._contract.functions.getUnselectedRequest(
            identifier, account).call()
        return {
            'block_number': call[0],
            'attestations_requested': call[1],
            'attestation_request_fee_token': call[2]
        }

    def is_attestation_expired(self, attestation_request_block_number: int) -> bool:
        """
        Checks if attestation request is expired

        Parameters:
            attestation_request_block_number: int
                Attestation Request Block Number to be checked
        """
        attestation_expity_block = self.attestation_expiry_blocks()
        current_block = self.web3.eth.getBlock().number
        return current_block >= attestation_request_block_number + attestation_expity_block

    def get_attestation_issuers(self, identifier: str, account: str) -> list:
        """
        Returns the issuers of attestations for a phoneNumber/account combo

        Parameters:
            identifier: str
                Attestation identifier (e.g. phone hash)
            account: str
                Address of the account
        """
        return self._contract.functions.getAttestationIssuers().call()

    def get_attestation_state(self, identifier: str, account: str, issuer: str) -> dict:
        """
        Returns the attestation state of a phone number/account/issuer tuple

        Parameters:
            identifier: str
                Attestation identifier (e.g. phone hash)
            account: str
                Address of the account
            issuer: str
        """
        call = self._contract.functions.getAttestationState(
            identifier, account, issuer).call()
        return {'attestation_state': call[0]}

    def get_attestation_stat(self, identifier: str, account: str) -> dict:
        """
        Returns the attestation stats of a identifer/account pair

        Parameters:
            identifier: str
                Attestation identifier (e.g. phone hash)
            account: str
                Address of the account
        """
        call = self._contract.functions.getAttestationStats(
            identifier, account).call()
        return {'completed': call[0], 'total': call[1]}

    def get_verified_status(self, identifer: str, account: str, num_attestations_required: int = None, attestation_threshold: int = None):
        """
        Returns the verified status of an identifier/account pair indicating whether the attestation
        stats for a given pair are completed beyond a certain threshold of confidence (aka "verified")

        Parameters:
            identifier: str
                Attestation identifier (e.g. phone hash)
            account: str
                Address of the account
            num_attestations_required: int
                Optional number of attestations required.  Will default to
                hardcoded value if absent
            attestation_threshold: int
                Optional threshold for fraction attestations completed. Will
                default to hardcoded value if absent
        """
        attestation_stats = self.get_attestation_stat(identifer, account)
        return attestations_utils.is_account_considered_verified(attestation_stats, num_attestations_required, attestation_threshold)

    def get_attestation_fee_required(self, attestations_requested: int) -> int:
        """
        Calculates the amount of StableToken required to request Attestations

        Parameters:
            attestations_requested: int
                The number of attestations to request
        """
        token_address = self.registry.load_contract_by_name('StableToken')
        attestation_fee = self._contract.functions.getAttestationRequestFee(
            token_address).call()
        return attestation_fee * attestations_requested

    def approve_attestation_fee(self, attestations_requested: int) -> str:
        """
        Approves the necessary amount of StableToken to request Attestations

        Parameters:
            attestations_requested: int
                The number of attestations to request
        """
        token_contract = self.create_and_get_contract_by_name('StableToken')
        fee = self.get_attestation_fee_required(attestations_requested)
        return token_contract.approve(self.address, fee)

    def get_actionable_attestations(self, identifier: str, account: str) -> list:
        """
        Returns an array of attestations that can be completed, along with the issuers' attestation
        service urls

        Parameters:
            identifier: str
                Attestation identifier (e.g. phone hash)
            account: str
                Address of the account
        """
        result = self._contract.functions.getCompletableAttestations(
            identifier, account).call()
        attestations = self.parse_get_completable_attestations(result)
        results = []
        for attestation in attestations:
            results.append(self.is_issuer_running_attestation_service(
                attestation['block_number'], attestation['issuer'], attestation['metadata_url']))

        return [attest['result'] for attest in results if attest['is_valid']]

    def get_non_compliant_issuers(self, identifier: str, account: str) -> list:
        """
        Returns an array of issuer addresses that were found to not run the attestation service

        Parameters:
            identifier: str
                Attestation identifier (e.g. phone hash)
            account: str
                Address of the account
        """
        result = self._contract.functions.getCompletableAttestations(
            identifier, account).call()
        attestations = self.parse_get_completable_attestations(result)
        results = []
        for attestation in attestations:
            results.append(self.is_issuer_running_attestation_service(
                attestation['block_number'], attestation['issuer'], attestation['metadata_url']))

        return [attest['issuer'] for attest in results if not attest['is_valid']]

    def complete(self, identifier: str, account: str, issuer: str, code: str) -> str:
        """
        Completes an attestation with the corresponding code

        Parameters:
            identifier: str
                Attestation identifier (e.g. phone hash)
            account: str
                Address of the account
            issuer: str
                The issuer of the attestation
            code: str
                The code received by the validator (signature)
        Returns:
            Transaction hash
        """
        accounts_contract = self.create_and_get_contract_by_name('Accounts')
        attestation_signer = accounts_contract.get_attestation_signer(issuer)

        message = self.web3.soliditySha3(['bytes32', 'address'], [identifier, account]).hex()
        message = encode_defunct(hexstr=message)
        signer_address = Account.recoverHash(message, signature=code)

        if signer_address != attestation_signer:
            raise Exception("Signature was not signed by attestation signer")

        signature_bytes = HexBytes(code)
        signature_bytes_standard = to_standard_signature_bytes(signature_bytes)
        signature_obj = Signature(signature_bytes=signature_bytes_standard)
        v, r, s = signature_obj.vrs
        func_call = self._contract.functions.complete(identifier, v, r, s)

        return self.__wallet.send_transaction(func_call)

    def find_matching_issuer(self, identifier: str, account: str, code: str, issuers: list) -> str:
        """
        Given a list of issuers, finds the matching issuer for a given code

        Parameters:
            identifier: str
                Attestation identifier (e.g. phone hash)
            account: str
                Address of the account
            code: str
                The code received by the validator (signature)
            issuers: list
                The list of potential issuers
        """
        accounts_contract = self.create_and_get_contract_by_name('Accounts')
        message = self.web3.soliditySha3(['bytes32', 'address'], [identifier, account]).hex()
        message = encode_defunct(hexstr=message)
        signer_address = Account.recoverHash(message, signature=code)

        for issuer in issuers:
            attestation_signer = accounts_contract.get_attestation_signer(issuer)

            if attestation_signer == signer_address:
                return issuer
        return None

    def get_config(self, tokens: list) -> dict:
        """
        Returns the current configuration parameters for the contract

        Parameters:
            tokens: list
                List of tokens used for attestation fees
        """
        fees = []
        for token in tokens:
            fee = self.attestation_request_fees(token)
            fees.append({'fee': fee, 'address': token})
        
        return {
            'attestation_expiry_blocks': self.attestation_expiry_blocks(),
            'attestation_request_fees': fees
        }

    def lookup_identifiers(self, identifiers: list) -> dict:
        """
        Lookup mapped wallet addresses for a given list of identifiers

        Parameters:
            identifiers: list
                Attestation identifiers (e.g. phone hashes)
        """
        stats = self._contract.functions.batchGetAttestationStats(identifiers).call()

        matches = stats[0]
        addresses = stats[1]
        completed = stats[2]
        total = stats[3]

        result = {}
        r_index = 0

        for i, identifier in enumerate(identifiers):
            number_of_matches = matches[i]
            if number_of_matches == 0:
                continue

            matching_addresses = {}
            for _ in range(number_of_matches):
                matching_address = addresses[r_index]
                matching_addresses[matching_address] = {
                    'completed': completed[r_index],
                    'total': total[r_index]
                }
                r_index += 1
            result[identifier] = matching_addresses
        
        return result

    def request_new_attestation(self, identifer: str, attestations_requested: int) -> str:
        """
        Requests a new attestation

        Parameters:
            identifer: str
                Attestation identifier (e.g. phone hash)
            attestations_requested: int
                The number of attestations to request
        Returns:
            Transaction hash
        """
        token_address = self.registry.load_contract_by_name('StableToken')['address']
        func_call = self._contract.functions.request(identifer, attestations_requested, token_address)

        return self.__wallet.send_transaction(func_call)

    def select_issuers(self, identifier: str) -> str:
        """
        Selects the issuers for previously requested attestations for a phone number

        Parameters:
            identifier: str
                Attestation identifier (e.g. phone hash)
        Returns:
            Transaction hash
        """
        func_call = self._contract.functions.selectIssuers()
        return self.__wallet.send_transaction(func_call)

    def reveal_phone_number_to_issuer(self, phone_number: str, account: str, issuer: str, service_url: str, pepper: str = None, sms_retriver_app_sig: str = None) -> dict:
        body = {'account': account,
                'phoneNumber': phone_number,
                'issuer': issuer,
                'salt': pepper,
                'smsRetrieverAppSig': sms_retriver_app_sig}
        return requests.post(service_url.rstrip('/') + 'attestations', body)

    def validate_attestation_code(self, identifier: str, account: str, issuer: str, code: str) -> bool:
        """
        Validates a given code by the issuer on-chain

        Parameters:
            identifier: str
                Attestation identifier (e.g. phone hash)
            account: str
                The address of the account which requested attestation
            issuer: str
                The address of the issuer of the attestation
            code: str
                The code send by the issuer
        """
        accounts_contract = self.create_and_get_contract_by_name('Accounts')
        attestation_signer = accounts_contract.get_attestation_signer(issuer)

        message = self.web3.soliditySha3(['bytes32', 'address'], [identifier, account]).hex()
        message = encode_defunct(hexstr=message)
        signer_address = Account.recoverHash(message, signature=code)

        if signer_address != attestation_signer:
            raise Exception("Signature was not signed by attestation signer")
        
        signature_bytes = HexBytes(code)
        signature_bytes_standard = to_standard_signature_bytes(signature_bytes)
        signature_obj = Signature(signature_bytes=signature_bytes_standard)
        v, r, s = signature_obj.vrs

        result = self._contract.functions.validateAttestationCode(identifier, account, v, r, s).call()

        return result != self.null_address

    def get_attestation_service_status(self, validator: dict) -> dict:
        """
        Gets the relevant attestation service status for a validator

        Parameters:
            validator: dict
                Validator to get the attestation service status for
        """
        accounts_contract = self.create_and_get_contract_by_name('Accounts')
        has_attestation_signer = accounts_contract.has_authorized_attestation_signer(validator['address'])
        attestation_signer = accounts_contract.get_attestation_signer(validator['address'])

        attestation_service_url = ''

        ret = {
            'has_attestation_signer': has_attestation_signer,
            'attestation_signer': attestation_signer,
            'attestation_service_url': None,
            'ok_status': False,
            'error': None,
            'sms_providers': [],
            'blacklisted_region_code': [],
            'right_account': False,
            'metadata_url': None,
            'state': self.attestation_service_status_state['no_attestation_signer'],
            'version': None,
            'age_of_latest_block': None
        }
        ret.update(validator)

        if not has_attestation_signer:
            return ret
        
        metadata_url = accounts_contract.get_metadata_url(validator['address'])

        if not metadata_url:
            ret['state'] = self.attestation_service_status_state['no_metadata_url']
        else:
            ret['metadata_url'] = metadata_url
        
        try:
            metadata = attestations_utils.fetch_from_url(self.web3, metadata_url)
            attestation_service_url_claim = [claim for claim in metadata['claims'] if claim['type'] == attestations_utils.CLAIM_TYPES['attestation_service_url']]
            
            if not attestation_service_url_claim:
                ret['state'] = self.attestation_service_status_state['no_attestation_service_url']
                return ret
            
            attestation_service_url = attestation_service_url_claim[0]['url']
        except:
            ret['state'] = self.attestation_service_status_state['invalid_metadata']
            ret['error'] = sys.exc_info()[1]
            return ret
        
        ret['attestation_service_url'] = attestation_service_url

        try:
            status_response = requests.get(attestation_service_url.rstrip('/') + 'status')

            if status_response.status_code != 200:
                ret['state'] = self.attestation_service_status_state['unreachable_attestation_service']
                return ret
            
            ret['ok_status'] = True
            status_response_body = status_response.json()
            ret['sms_providers'] = status_response_body['smsProviders']
            ret['blacklisted_region_code'] = status_response_body['blacklistedRegionCodes']
            ret['right_account'] = status_response_body['accountAddress'] == validator['address']
            ret['state'] = self.attestation_service_status_state['valid']
            ret['version'] = status_response['version']
            ret['age_of_latest_block'] = status_response_body['ageOfLatestBlock']
            return ret
        except:
            ret['state'] = self.attestation_service_status_state['unreachable_attestation_service']
            ret['error'] = sys.exc_info()[1]
            return ret
    
    def revoke(self, identifier: str, account: str) -> str:
        try:
            accounts = self._contract.functions.lookupAccountsForIdentifier(identifier).call()
            idx = accounts.index(account)
            func_call = self._contract.functions.revoke(identifier, idx)
            return self.__wallet.send_transaction(func_call)
        except:
            raise Exception("Account not found in identifier's accounts")

    def is_issuer_running_attestation_service(self, block_number: int, issuer: str, metadata_url: str) -> dict:
        try:
            metadata = attestations_utils.fetch_from_url(
                self.web3, metadata_url)
            attestation_service_url_claim = [
                el for el in metadata['claims'] if el['type'] == attestations_utils.CLAIM_TYPES['attestation_service_url']]
            if not attestation_service_url_claim:
                raise Exception(
                    f"No attestation service URL registered for {issuer}")

            name_claim = [el for el in metadata['claims']
                          if el['type'] == attestations_utils.CLAIM_TYPES['name']]

            return {
                'is_valid': True,
                'result': {
                    'block_number': block_number,
                    'issuer': issuer,
                    'attestation_service_url': attestation_service_url_claim[0]['url'],
                    'name': name_claim[0]['name'] if name_claim else None
                }
            }
        except:
            return {'is_valid': False, 'issuer': issuer}
