import time
import unittest
import json
import random

from web3 import Web3

from celo_sdk.kit import Kit
from celo_sdk.tests import test_data


class TestSortedOraclesWrapper(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.kit = Kit('http://localhost:8544')
        self.sorted_oracles_wrapper = self.kit.base_wrapper.create_and_get_contract_by_name(
            'SortedOracles')
        self.kit.w3.eth.defaultAccount = test_data.oracle_address
        self.kit.wallet_add_new_key = test_data.oracle
        self.kit.wallet.sign_with_provider = True
        self.accounts = self.kit.w3.eth.accounts
        for _, v in test_data.deriv_pks.items():
            self.kit.wallet_add_new_key = v

        self.kit.w3.eth.defaultAccount = self.accounts[0]
        self.kit.wallet_change_account = self.accounts[0]

        with open('celo_sdk/tests/dev_net_conf.json') as file:
            data = json.load(file)
            self.net_config = data

        self.stable_token_oracles = self.net_config['stableToken']['oracles']
        self.oracle_address = test_data.oracle_address

        self.oracle_token_address = self.kit.base_wrapper.create_and_get_contract_by_name('StableToken').address
        self.non_oracle_address = self.accounts[0]

    def report_as_oracles(self, oracles: list, rates: list = None):
        local_rates = []
        if rates == None:
            for _ in oracles:
                local_rates.append(random.randint(1, 10))
        else:
            local_rates = rates
        
        for rate, oracle in zip(local_rates, oracles):
            tx = self.sorted_oracles_wrapper.report('StableToken', rate, oracle)
            time.sleep(3)
    
    def setup_expired_and_not_expired_reports(self, expired_oracles: list):
        expiry_seconds = self.sorted_oracles_wrapper.report_expiry_seconds()
        self.report_as_oracles(expired_oracles)
        fresh_oracles = [el for el in self.stable_token_oracles if el not in expired_oracles]
        self.report_as_oracles(fresh_oracles)
    
    def test_should_be_able_to_report(self):
        value = 16
        initial_rates = self.sorted_oracles_wrapper.get_rates('StableToken')

        tx = self.sorted_oracles_wrapper.report('StableToken', value, self.oracle_address)

        resulting_rates = self.sorted_oracles_wrapper.get_rates('StableToken')

        self.assertNotEqual(resulting_rates, initial_rates)

    def test_passes_correct_lesser_and_greater_keys(self):
        value = 16
        rates = [15, 20, 17]
        self.report_as_oracles(self.stable_token_oracles, rates)

        expected_lesser_key = self.stable_token_oracles[0]
        expected_greater_key = self.stable_token_oracles[2]

        tx = self.sorted_oracles_wrapper.report('StableToken', value, self.oracle_address)

        self.assertTrue(tx)

    def test_inserts_new_record_in_the_right_plase(self):
        rates = [15, 20, 17]
        self.report_as_oracles(self.stable_token_oracles, rates)
        value = 16
        expected_oracle_order = [self.stable_token_oracles[1], self.stable_token_oracles[2], self.oracle_address, self.stable_token_oracles[0]]

        tx = self.sorted_oracles_wrapper.report('StableToken', value, self.oracle_address)

        resulting_rates = self.sorted_oracles_wrapper.get_rates('StableToken')

        self.assertEqual([el['address'] for el in resulting_rates], expected_oracle_order)
    

    def test_reporting_from_non_oracle_address(self):
        value = 16
        tx = self.sorted_oracles_wrapper.report('StableToken', value, self.non_oracle_address)

    def test_should_not_change_the_list_of_rates(self):
        value = 16
        initial_rates = self.sorted_oracles_wrapper.get_rates('StableToken')
        try:
            tx = self.sorted_oracles_wrapper.report('StableToken', value, self.non_oracle_address)
        except:
            # We don't need to do anything with this error other than catch it so
            # it doesn't fail this test
            pass
        finally:
            resulting_rates = self.sorted_oracles_wrapper.get_rates('StableToken')
            self.assertEqual(resulting_rates, initial_rates)

    def test_successfully_remove_report(self):
        expired_oracles = self.stable_token_oracles[0: 2]
        self.setup_expired_and_not_expired_reports(expired_oracles)
        initial_report_count = self.sorted_oracles_wrapper.num_rates('StableToken')
        
        self.kit.w3.eth.defaultAccount = self.oracle_address
        self.kit.wallet_change_account = self.oracle_address
        tx = self.sorted_oracles_wrapper.remove_expired_reports('StableToken', 1)

        self.assertEqual(self.sorted_oracles_wrapper.num_rates('StableToken'), initial_report_count - 1)

    def test_remove_only_expired_reports(self):
        expired_oracles = self.stable_token_oracles[0: 2]
        self.setup_expired_and_not_expired_reports(expired_oracles)
        initial_report_count = self.sorted_oracles_wrapper.num_rates('StableToken')

        to_remove = len(expired_oracles) + 1
        self.kit.w3.eth.defaultAccount = self.oracle_address
        self.kit.wallet_change_account = self.oracle_address
        tx = self.sorted_oracles_wrapper.remove_expired_reports('StableToken', to_remove)

        self.assertEqual(self.sorted_oracles_wrapper.num_rates('StableToken'), initial_report_count - len(expired_oracles))

    def test_should_not_remove_any_reports_when_they_are_not_expired(self):
        expired_oracles = self.stable_token_oracles[0: 2]
        self.setup_expired_and_not_expired_reports(expired_oracles)
        initial_report_count = self.sorted_oracles_wrapper.num_rates('StableToken')

        self.report_as_oracles(self.stable_token_oracles)

        initial_report_count = self.sorted_oracles_wrapper.num_rates('StableToken')
        self.kit.w3.eth.defaultAccount = self.oracle_address
        self.kit.wallet_change_account = self.oracle_address
        tx = self.sorted_oracles_wrapper.remove_expired_reports('StableToken', 1)

        self.assertEqual(self.sorted_oracles_wrapper.num_rates('StableToken'), initial_report_count)

    def test_when_at_least_one_expired_report_exist(self):
        self.setup_expired_and_not_expired_reports([self.oracle_address])
        is_expired, address = self.sorted_oracles_wrapper.is_oldest_report_expired('StableToken')

        self.assertTrue(is_expired)
        self.assertEqual(address, self.stable_token_oracles[0])

    def test_when_the_oldest_is_not_expired(self):
        self.report_as_oracles(self.stable_token_oracles)
        is_expired, address = self.sorted_oracles_wrapper.is_oldest_report_expired('StableToken')

        self.assertFalse(is_expired)
        self.assertEqual(address, self.stable_token_oracles[0])

    def test_sbat_get_rates(self):
        expected_rates = [2, 1.5, 1, 0.5]
        self.report_as_oracles(self.stable_token_oracles, expected_rates)

        actual_rates = self.sorted_oracles_wrapper.get_rates('StableToken')

        self.assertTrue(len(actual_rates) > 0)

        for rate in actual_rates:
            self.assertTrue('address' in rate)
            self.assertTrue('rate' in rate)
            self.assertTrue('median_relation' in rate)

    def test_correct_rate(self):
        expected_rates = [2, 1.5, 1, 0.5]
        self.report_as_oracles(self.stable_token_oracles, expected_rates)

        response = self.sorted_oracles_wrapper.get_rates('StableToken')
        actual_rates = [el['rate'] for el in response]

        self.assertEqual(actual_rates, expected_rates)

    def test_check_oracle_positive(self):
        self.assertTrue(self.sorted_oracles_wrapper.is_oracle('StableToken', self.oracle_address))

    def test_check_oracle_negatice(self):
        self.assertFalse(self.sorted_oracles_wrapper.is_oracle('StableToken', self.non_oracle_address))

    def test_num_rates(self):
        self.assertEqual(self.sorted_oracles_wrapper.num_rates('StableToken'), 1)

    def test_median_rate(self):
        returned_median = self.sorted_oracles_wrapper.median_rate('StableToken')

        self.assertEqual(returned_median['rate'], self.net_config['stableToken']['goldPrice'])

    def test_report_expiry_seconds(self):
        result = self.sorted_oracles_wrapper.report_expiry_seconds()

        self.assertEqual(result, self.net_config['oracles']['reportExpiry'])

    def test_get_stable_token_rates(self):
        usd_rates_result = self.sorted_oracles_wrapper.get_stable_token_rates()
        get_rates_result = self.sorted_oracles_wrapper.get_rates('StableToken')

        self.assertEqual(usd_rates_result, get_rates_result)

    def test_report_stable_token(self):
        tx = self.sorted_oracles_wrapper.report_stable_token(14, self.oracle_address)

        self.assertTrue(tx)
