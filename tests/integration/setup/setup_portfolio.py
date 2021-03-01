import lusid.models as models
import lusid
from lusid import ApiException


def setup_portfolio(api_factory, portfolio_scope, portfolio_code, portfolio_created_date, properties: dict):
    # Create portfolio and assign the corp action source
    portfolio_request = models.CreateTransactionPortfolioRequest(
        display_name=portfolio_code,
        code=portfolio_code,
        base_currency="GBP",
        created=portfolio_created_date,
        properties=properties
    )

    try:
        api_factory.build(lusid.api.TransactionPortfoliosApi).create_portfolio(
            scope=portfolio_scope,
            create_transaction_portfolio_request=portfolio_request
        )
    except ApiException:
        print(f"Portfolio with code {portfolio_code} and scope {portfolio_scope} already exists")


def update_portfolio_properties():
    pass
