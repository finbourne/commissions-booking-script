import logging

from helpers.utilities import get_commission_rate_from_lookup
from transaction_helpers.transaction_upsertion import create_properties_request, create_upsert_transaction_request
import constants as const


def get_transaction_requests_from_input_transactions(input_transactions, country_prop, entity, broker):
    transaction_requests = []
    for input_transaction in input_transactions.values:
        country_property = input_transaction.properties.get(country_prop)

        # TODO: Consider whether to skip this or do something about it
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

# THE BELOW NOT IMPLEMENTED YET AND NOT COMPLETE
def filter_input_txn_if_commission_txn_exists(input_transactions, commission_transactions, **mapping_prop_values):
    filtered_transactions = []
    for input_transaction in input_transactions.values:

        if has_up_to_date_linked_commission_txn(input_transaction, commission_transactions):
            continue
        filtered_transactions.append(input_transaction)

    return {
        "values": filtered_transactions
    }


def has_up_to_date_linked_commission_txn(input_transaction, commission_transactions):
    for commission_transaction in commission_transactions.values:

        # That id property needs to come a global setting
        linked_transaction_prop = commission_transaction.properties.get(const.LINKING_PROPERTY)
        if not linked_transaction_prop:
            logging.info("There is no property called 'this should come from a global id' .. on this txn id ")
            continue
        linked_transaction_id = linked_transaction_prop.value.label_value

        # Find a way to correctly pass all mapping values
        commission_rate = get_commission_rate_from_lookup()

        if input_transaction.transaction_id == linked_transaction_id \
                and input_transaction.units == commission_transaction.units \
                and input_transaction.total_consideration.amount*commission_rate == commission_transaction.total_consideration.amount \
                and input_transaction.transaction_date == commission_transaction.transaction_date \
                and input_transaction.settlement_date == commission_transaction.settlement_date:
            return True

    return False
