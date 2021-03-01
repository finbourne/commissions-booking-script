import lusid.models as models
import lusid


def setup_transaction(api_factory, transaction_id, transaction_date, settlement_date, instrument_id, portfolio_scope,
                      portfolio_code, units, txn_type="Buy"):
    # Create a buy transaction in the portfolio
    price = 1
    transaction_request1 = models.TransactionRequest(
        transaction_id=transaction_id,
        type=txn_type,
        instrument_identifiers={"Instrument/default/ClientInternal": instrument_id},
        transaction_date=transaction_date,
        settlement_date=settlement_date,
        units=units,
        transaction_price=models.TransactionPrice(price=price),
        total_consideration=models.CurrencyAndAmount(amount=units*price, currency="GBP"),
        transaction_currency="GBP"
    )
    api_factory.build(lusid.api.TransactionPortfoliosApi).upsert_transactions(
        scope=portfolio_scope,
        code=portfolio_code,
        transaction_request=[
            transaction_request1
        ]
    )