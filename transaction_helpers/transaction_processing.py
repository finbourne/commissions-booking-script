import logging

from helpers.utilities import get_commission_rate_from_lookup
from transaction_helpers.transaction_upsertion import create_properties_request, create_upsert_transaction_request


def get_transaction_requests_from_input_transactions(input_transactions, country_prop, entity, broker):
    transaction_requests = []
    for input_transaction in input_transactions.values:
        country_property = input_transaction.properties.get(country_prop)

        if not country_property:
            logging.info(f"There is no property '{country_prop}' on the transaction with id "
                         f"'{input_transaction.transaction_id}'. Skipping.")
            continue

        country = country_property.value.label_value
        commission_rate = get_commission_rate_from_lookup(country, broker, entity)
        logging.info(f"creating/updating txn: {input_transaction.transaction_id}")

        # Create transaction request
        transaction_type = "Commission"
        instrument_identifier = "Instrument/default/Currency"
        properties = create_properties_request(input_transaction, transaction_type)
        # append request
        transaction_requests = transaction_requests + create_upsert_transaction_request(
            input_transaction, commission_rate, transaction_type, instrument_identifier, properties
        )
    return transaction_requests