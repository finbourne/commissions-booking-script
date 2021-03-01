import logging

import lusid


def get_input_transactions(
        api_factory, scope, portfolio_code, end_date_formatted: str, start_date_formatted: str, input_txn_filter,
        property_keys: list
):
    transactions_portfolios_api = api_factory.build(lusid.api.TransactionPortfoliosApi)

    # Consider paging this
    input_transactions = transactions_portfolios_api.get_transactions(
        scope=scope, code=portfolio_code, from_transaction_date=start_date_formatted,
        to_transaction_date=end_date_formatted, filter=input_txn_filter, property_keys=property_keys
    )

    if len(input_transactions.values) == 0:
        logging.info(
            f"There are no transactions between effective date ending {end_date_formatted} and starting '{start_date_formatted}"
        )

    return input_transactions
