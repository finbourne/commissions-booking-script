import json
import os
import time
import unittest

import lusid
from datetime import datetime

from main import get_input_transactions, check_or_create_commission_transactions
from tests.integration.setup.setup_instruments import setup_instruments
from tests.integration.setup.setup_portfolio import setup_portfolio
from tests.integration.setup.setup_properties import property_def
from tests.integration.setup.setup_transaction import setup_transaction
from helpers.utilities import create_commission_txn_type, check_or_create_property, get_commission_rate_from_lookup

api_factory = lusid.utilities.ApiClientFactory(
    app_name="commissions-tests-script",
    api_secrets_filename=os.getenv("FBN_SECRETS_PATH")
)
transactions_portfolios_api = api_factory.build(lusid.api.TransactionPortfoliosApi)
instruments_api = api_factory.build(lusid.api.InstrumentsApi)
portfolios_api = api_factory.build(lusid.api.PortfoliosApi)

commissions_config_path = os.path.abspath('./setup/commissions-config.json')
os.environ["FBN_COMMISSIONS_CONFIG_PATH"] = commissions_config_path

with open(commissions_config_path, 'r') as config:
    cfg = config.read()
    commissions_rate_config = json.loads(cfg)

# Instruments setup
instrument_test_name1 = "commissions-test-instrument1"
instrument_1_country = "UK"
instrument_test_name2 = "commissions-test-instrument2"
instrument_2_country = "US"
instrument_test_name3 = "commissions-test-instrument3"
instrument_3_country = "UK"

# Portfolios
portfolio_code = "commissions-integration-test"
portfolio_scope = "commissions-integration-test"
portfolio_created_date = "2000-01-05T00:00:00+00:00"
portfolio_broker = "UBS"
portfolio_entity = "entity1"

# Transactions
transaction_id1 = "transaction-id-test1"
transaction_date1 = "2021-01-01T00:00:00+00:00"
settlement_date1 = "2021-01-01T00:00:00+00:00"
input_transaction_units1 = 100

transaction_id2 = "transaction-id-test2"
transaction_date2 = "2020-12-01T00:00:00+00:00"
settlement_date2 = "2020-12-03T00:00:00+00:00"
input_transaction_units2 = 50

transaction_id3 = "transaction-id-test3"
transaction_date3 = "2020-10-01T00:00:00+00:00"
settlement_date3 = "2020-10-02T00:00:00+00:00"
input_transaction_units3 = 150

# Properties
entity_prop = "Portfolio/test/Entity"
broker_prop = "Portfolio/test/Broker"
country_prop = "Instrument/test/Country"
all_prop_keys = [entity_prop, broker_prop, country_prop]

date_now_iso_str = str(datetime.today().astimezone().isoformat())
commission_id_suffix = "_commission"


class CreateTaxTransactionsTests(unittest.TestCase):

    @classmethod
    def setUp(cls) -> None:
        create_commission_txn_type(api_factory)

        # setup property definitions
        check_or_create_property(api_factory, entity_prop)
        check_or_create_property(api_factory, broker_prop)
        check_or_create_property(api_factory, country_prop)
        type_property = "Transaction/generated/Type"
        check_or_create_property(api_factory, type_property)

        # setup instruments
        setup_instruments(
            api_factory, instrument_test_name1, instrument_test_name1,
            [property_def(country_prop, instrument_1_country)]
        )
        setup_instruments(
            api_factory, instrument_test_name2, instrument_test_name2,
            [property_def(country_prop, instrument_2_country)]
        )
        setup_instruments(
            api_factory, instrument_test_name3, instrument_test_name3,
            [property_def(country_prop, instrument_3_country)]
        )

        # setup portfolio
        portfolio_properties = {
            entity_prop: property_def(entity_prop, portfolio_entity),
            broker_prop: property_def(broker_prop, portfolio_broker)
        }
        setup_portfolio(api_factory, portfolio_scope, portfolio_code, portfolio_created_date, portfolio_properties)

        # setup transactions
        setup_transaction(api_factory, transaction_id1, transaction_date1, settlement_date1, instrument_test_name1,
                          portfolio_scope, portfolio_code, input_transaction_units1, txn_type="Buy")
        setup_transaction(api_factory, transaction_id2, transaction_date2, settlement_date2, instrument_test_name2,
                          portfolio_scope, portfolio_code, input_transaction_units2, txn_type="Sell")
        setup_transaction(api_factory, transaction_id3, transaction_date3, settlement_date3, instrument_test_name3,
                          portfolio_scope, portfolio_code, input_transaction_units3, txn_type="Buy")


    @classmethod
    def tearDown(cls) -> None:
        # Delete portfolio
        portfolios_api.delete_portfolio(
            scope=portfolio_scope,
            code=portfolio_code
        )

    def test_if_portfolio_set_up_correctly(self, **filter_args):
        # List portfolio contents
        filter_transactions = ""
        if filter_args.get("filter"):
            filter_transactions = filter_args.get("filter")
        input_transactions = get_input_transactions(
            api_factory, portfolio_scope, portfolio_code, date_now_iso_str, portfolio_created_date, filter_transactions,
            [country_prop]
        )

        self.assertEqual(len(input_transactions.values), 3)
        for input_transaction in input_transactions.values:
            self.assertTrue(
                input_transaction.transaction_id in [
                    transaction_id1,
                    transaction_id2,
                    transaction_id3]
            )
            if input_transaction.transaction_id == transaction_id1:
                self.assertEqual(input_transaction.type, "Buy")
                self.assertEqual(input_transaction.transaction_date.isoformat(), transaction_date1)
                self.assertEqual(input_transaction.settlement_date.isoformat(), settlement_date1)
                self.assertEqual(input_transaction.units, input_transaction_units1)
                self.assertEqual(input_transaction.properties[country_prop].value.label_value, instrument_1_country)
            if input_transaction.transaction_id == transaction_id2:
                self.assertEqual(input_transaction.type, "Sell")
                self.assertEqual(input_transaction.transaction_date.isoformat(), transaction_date2)
                self.assertEqual(input_transaction.settlement_date.isoformat(), settlement_date2)
                self.assertEqual(input_transaction.units, input_transaction_units2)
                self.assertEqual(input_transaction.properties[country_prop].value.label_value, instrument_2_country)
            if input_transaction.transaction_id == transaction_id3:
                self.assertEqual(input_transaction.type, "Buy")
                self.assertEqual(input_transaction.transaction_date.isoformat(), transaction_date3)
                self.assertEqual(input_transaction.settlement_date.isoformat(), settlement_date3)
                self.assertEqual(input_transaction.units, input_transaction_units3)
                self.assertEqual(input_transaction.properties[country_prop].value.label_value, instrument_3_country)

    def test_commission_transactions_are_created_when_running_script(self):
        check_or_create_commission_transactions(
            portfolio_scope, portfolio_code, date_now_iso_str, portfolio_created_date, api_factory, portfolio_entity,
            portfolio_broker
        )

        # Test the commission transaction now, and test whether original transactions exist below
        txn_filter = "type in 'Commission'"
        input_transactions = get_input_transactions(
            api_factory, portfolio_scope, portfolio_code, date_now_iso_str, portfolio_created_date, txn_filter,
            [country_prop]
        )

        self.assertEqual(len(input_transactions.values), 3)
        for input_transaction in input_transactions.values:
            self.assertTrue(
                input_transaction.transaction_id in [
                    transaction_id1 + commission_id_suffix,
                    transaction_id2 + commission_id_suffix,
                    transaction_id3 + commission_id_suffix,
                ]
            )
            if input_transaction.transaction_id == transaction_id1 + commission_id_suffix:
                self.assertEqual(input_transaction.type, "Commission")
                self.assertEqual(input_transaction.transaction_date.isoformat(), transaction_date1)
                self.assertEqual(input_transaction.settlement_date.isoformat(), settlement_date1)
                self.assertEqual(
                    input_transaction.units,
                    input_transaction_units1
                    * commissions_rate_config[instrument_1_country][portfolio_broker][portfolio_entity]
                )
            if input_transaction.transaction_id == transaction_id2 + commission_id_suffix:
                self.assertEqual(input_transaction.type, "Commission")
                self.assertEqual(input_transaction.transaction_date.isoformat(), transaction_date2)
                self.assertEqual(input_transaction.settlement_date.isoformat(), settlement_date2)
                self.assertEqual(
                    input_transaction.units,
                    input_transaction_units2
                    * commissions_rate_config[instrument_2_country][portfolio_broker][portfolio_entity]
                )
            if input_transaction.transaction_id == transaction_id3 + commission_id_suffix:
                self.assertEqual(input_transaction.type, "Commission")
                self.assertEqual(input_transaction.transaction_date.isoformat(), transaction_date3)
                self.assertEqual(input_transaction.settlement_date.isoformat(), settlement_date3)
                self.assertEqual(
                    input_transaction.units,
                    input_transaction_units3
                    * commissions_rate_config[instrument_3_country][portfolio_broker][portfolio_entity]
                )

            # Test that initial portfolio transactions still exist and are unchanged
            self.test_if_portfolio_set_up_correctly(filter="type in 'Buy', 'Sell', 'Purchase'")

    def test_transactions_are_unchanged_when_running_script_twice(self):
        self.test_commission_transactions_are_created_when_running_script()
        self.test_commission_transactions_are_created_when_running_script()

    def test_commission_transactions_are_created_when_new_input_transaction_is_added(self, **kwargs):
        new_transaction_id = "transaction-id-test-new-test"
        new_transaction_date = "2021-01-15T00:00:00+00:00"
        new_settlement_date = "2021-01-16T00:00:00+00:00"
        new_input_transaction_units = 150
        expected_instrument_country = "US"

        if not kwargs.get("skip_run_script_at_start"):
            self.test_commission_transactions_are_created_when_running_script()

        setup_transaction(
            api_factory, new_transaction_id, new_transaction_date, new_settlement_date,
            instrument_test_name2, portfolio_scope, portfolio_code, new_input_transaction_units, txn_type="Buy"
        )

        check_or_create_commission_transactions(
            portfolio_scope, portfolio_code, date_now_iso_str, portfolio_created_date, api_factory, portfolio_entity,
            portfolio_broker
        )

        txn_filter = "type in 'Commission'"
        input_transactions = get_input_transactions(
            api_factory, portfolio_scope, portfolio_code, date_now_iso_str, portfolio_created_date, txn_filter,
            [country_prop]
        )

        self.assertEqual(len(input_transactions.values), 4)
        for input_transaction in input_transactions.values:
            self.assertTrue(
                input_transaction.transaction_id in [
                    transaction_id1 + commission_id_suffix,
                    transaction_id2 + commission_id_suffix,
                    transaction_id3 + commission_id_suffix,
                    new_transaction_id + commission_id_suffix
                ]
            )
            if input_transaction.transaction_id == new_transaction_id + commission_id_suffix:
                self.assertEqual(input_transaction.type, "Commission")
                self.assertEqual(input_transaction.transaction_date.isoformat(), new_transaction_date)
                self.assertEqual(input_transaction.settlement_date.isoformat(), new_settlement_date)
                self.assertEqual(
                    input_transaction.units,
                    new_input_transaction_units
                    * commissions_rate_config[expected_instrument_country][portfolio_broker][portfolio_entity]
                )

    def test_commission_value_after_input_transaction_units_has_been_modified(self):
        self.test_commission_transactions_are_created_when_running_script()

        # Upsert the same transaction but change units
        updated_units = 150
        setup_transaction(
            api_factory, transaction_id1, transaction_date1, settlement_date1, instrument_test_name1,
            portfolio_scope, portfolio_code, updated_units, txn_type="Buy"
        )

        check_or_create_commission_transactions(
            portfolio_scope, portfolio_code, date_now_iso_str, portfolio_created_date, api_factory, portfolio_entity,
            portfolio_broker
        )

        # Give the script a second to update transaction
        time.sleep(2)

        txn_filter = "type in 'Commission'"
        input_transactions = get_input_transactions(
            api_factory, portfolio_scope, portfolio_code, date_now_iso_str, portfolio_created_date, txn_filter,
            [country_prop]
        )

        self.assertEqual(len(input_transactions.values), 3)
        for input_transaction in input_transactions.values:
            self.assertTrue(
                input_transaction.transaction_id in [
                    transaction_id1 + commission_id_suffix,
                    transaction_id2 + commission_id_suffix,
                    transaction_id3 + commission_id_suffix
                ]
            )
            if input_transaction.transaction_id == transaction_id1 + commission_id_suffix:
                self.assertEqual(input_transaction.type, "Commission")
                self.assertEqual(input_transaction.transaction_date.isoformat(), transaction_date1)
                self.assertEqual(input_transaction.settlement_date.isoformat(), settlement_date1)
                self.assertEqual(
                    input_transaction.units,
                    updated_units
                    * commissions_rate_config[instrument_1_country][portfolio_broker][portfolio_entity]
                )

    def test_setup_portfolio_with_transactions_then_modify_a_transaction_and_then_add_another_transaction(self):
        self.test_commission_transactions_are_created_when_running_script()
        self.test_commission_value_after_input_transaction_units_has_been_modified()
        self.test_commission_transactions_are_created_when_new_input_transaction_is_added(skip_run_script_at_start=True)


if __name__ == '__main__':
    unittest.main()
