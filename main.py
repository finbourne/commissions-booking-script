import argparse
import logging
import os
import sys

import lusid
from datetime import datetime, timedelta

from helpers.lusid_drive_util import get_file_from_drive
from helpers.utilities import check_or_create_property, create_commission_txn_type, setup_logging
from transaction_helpers.transaction_processing import get_transaction_requests_from_input_transactions, \
    filter_input_txn_if_commission_txn_exists
from transaction_helpers.transaction_retrieval import get_input_transactions
from transaction_helpers.transaction_upsertion import upsert_transactions
import constants as const

setup_logging()


def check_or_create_commission_transactions(scope, portfolio_code, end_date: str, start_date: str, api_factory,
                                            entity, broker):
    logging.info(f"Beginning to process portfolio with scope '{scope}' and portfolio code '{portfolio_code}'")
    logging.info(f"The 'to' date is '{end_date}' and 'from' date is '{start_date}'")
    logging.info(f"The broker is '{broker}' and entity is '{entity}'")

    input_transactions = get_input_transactions(
        api_factory, scope, portfolio_code, end_date, start_date, const.INPUT_TXN_FILTER, [const.COUNTRY_PROPERTY]
    )

    transaction_requests = get_transaction_requests_from_input_transactions(input_transactions, const.COUNTRY_PROPERTY, entity, broker)

    response = upsert_transactions(api_factory, scope, portfolio_code, transaction_requests)

    # Handle failed transaction upserts here
    logging.info(f"Upserted transactions.")
    logging.info("Transaction updated/created")


def main(argv):
    ap = argparse.ArgumentParser(description="Get arguments from command line")
    ap.add_argument('-s', '--scope', help='Scope of the data being uploaded', required=True)
    ap.add_argument('-c', '--portfolio-code', required=True)
    # ap.add_argument('-tz', '--timezone', default=0)
    ap.add_argument('-dt', '--datetime-iso', help="must be in iso format",
                    default=str(datetime.today().astimezone().isoformat()))
    ap.add_argument('-d', '--days-going-back')

    args = vars(ap.parse_args(args=argv[1:]))
    scope = args["scope"]
    portfolio_code = args["portfolio_code"]
    datetime_iso = args["datetime_iso"]
    days_going_back = args["days_going_back"]

    api_factory = lusid.utilities.ApiClientFactory(
        app_name="commissions-script",
        api_secrets_filename=os.getenv("FBN_SECRETS_PATH")
    )
    create_commission_txn_type(api_factory)

    # TODO: These properties need to come from a global config file
    type_property = "Transaction/generated/Type"
    linked_id_property = "Transaction/generated/LinkedTransactionId"
    check_or_create_property(api_factory, type_property)
    check_or_create_property(api_factory, linked_id_property)


    # Cache config file:
    config_name = "commission-config.json"
    config_path = "CommissionConfig"
    config_file = get_file_from_drive(config_path, config_name)
    os.environ["FBN_COMMISSIONS_CONFIG_PATH"] = config_file

    # Set up portfolio properties
    entity_prop = const.ENTITY_PROPERTY
    broker_prop = const.BROKER_PROPERTY
    country_prop = const.COUNTRY_PROPERTY
    check_or_create_property(api_factory, entity_prop)
    check_or_create_property(api_factory, broker_prop)
    check_or_create_property(api_factory, country_prop)

    # Get portfolio property values
    get_portfolio = api_factory.build(lusid.api.PortfoliosApi).get_portfolio(
        scope=scope, code=portfolio_code, property_keys=[entity_prop, broker_prop]
    )
    entity_prop_value = get_portfolio.properties[entity_prop].value.label_value
    broker_prop_value = get_portfolio.properties[broker_prop].value.label_value

    # Process dates
    end_date = datetime.today().astimezone()
    end_date_formatted = str(end_date.isoformat())
    if datetime_iso:
        end_date_formatted = datetime_iso

    portfolio_created_date = get_portfolio.created
    start_date = portfolio_created_date
    if days_going_back:
        start_date = end_date + timedelta(days=-int(days_going_back))
    start_date_formatted = str(start_date.isoformat())

    # Loop over portfolios if you wish here:
    check_or_create_commission_transactions(
        scope, portfolio_code, end_date_formatted, start_date_formatted, api_factory, entity_prop_value,
        broker_prop_value
    )


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main(sys.argv)

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
