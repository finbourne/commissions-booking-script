from math import ceil

import lusid
from lusid import models


def create_properties_request(input_transaction, transaction_type) -> dict:
    properties = {
        # Remove this
        "Transaction/generated/Commission": models.PerpetualProperty(
            key="Transaction/generated/Commission",
            value=models.PropertyValue(label_value=input_transaction.transaction_id)
        ),
        "Transaction/generated/Type": models.PerpetualProperty(
            key="Transaction/generated/Type",
            value=models.PropertyValue(label_value=transaction_type)
        ),
        # TODO: This property to come from a global config file
        "Transaction/generated/LinkedTransactionId": models.PerpetualProperty(
            key="Transaction/generated/LinkedTransactionId",
            value=models.PropertyValue(label_value=input_transaction.transaction_id)
        )
    }

    return properties


def create_upsert_transaction_request(input_transaction, commission_rate, transaction_type, instrument_identifier, properties: dict) -> list:
    transaction_id_suffix = "_commission"
    # transaction_type = "Commission"
    # instrument_identifier = "Instrument/default/Currency"

    request = models.TransactionRequest(
        transaction_id=f"{input_transaction.transaction_id}{transaction_id_suffix}",
        transaction_date=str(input_transaction.transaction_date.isoformat()),
        # Is this transaction date or settlement date?
        settlement_date=str(input_transaction.settlement_date.isoformat()),
        type=transaction_type,
        instrument_identifiers={instrument_identifier: input_transaction.transaction_currency},
        total_consideration=models.CurrencyAndAmount(
            amount=input_transaction.total_consideration.amount * commission_rate,
            currency=input_transaction.transaction_currency),
        units=input_transaction.units * commission_rate,
        transaction_currency=input_transaction.transaction_currency,
        properties=properties
    )
    return [request]


def upsert_transactions(api_factory, scope, portfolio_code, transactions: list, batch_size=5000):

    responses = []
    batches = ceil(len(transactions)/batch_size)
    for i in range(0, batches):
        print(f"\nBATCH NUMBER {i+1}:\n")
        response = api_factory.build(lusid.api.TransactionPortfoliosApi).upsert_transactions(
            scope=scope, code=portfolio_code, transaction_request=transactions[i:i+batch_size]
        )
        # Response
        print(f"TYPE OF RESPONSE IS {type(response)}")
        responses.append(response)

    return responses
