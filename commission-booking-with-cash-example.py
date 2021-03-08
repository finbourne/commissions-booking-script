import json
import os
import lusid
from lusid import models, ApiException


def setup_instruments(lusid_api_factory, instrument_name, instrument_client_internal, properties: list):
    # Create an instrument
    test_instrument_req1 = models.InstrumentDefinition(
        name=instrument_name,
        identifiers={"ClientInternal": models.InstrumentIdValue(value=instrument_client_internal)},
        properties=properties
    )
    lusid_api_factory.build(lusid.api.InstrumentsApi).upsert_instruments(
        request_body={"request1": test_instrument_req1}
    )


def property_def(full_property, label_value):
    prop = models.ModelProperty(
        key=full_property,
        value=models.PropertyValue(
            label_value=label_value
        )
    )

    return prop


def check_or_create_property(lusid_api_factory, property_key):
    split_prop = property_key.split("/")
    if len(split_prop) != 3:
        raise ValueError(f"Invalid Value: {property_key}. The property key must have exactly two '/' slashes!")

    domain = split_prop[0]
    scope = split_prop[1]
    code = split_prop[2]

    prop_def_req = models.CreatePropertyDefinitionRequest(
        domain=domain,
        scope=scope,
        code=code,
        display_name=f"{code}",
        data_type_id=models.ResourceId(scope="system", code="string")
    )
    try:
        lusid_api_factory.build(lusid.api.PropertyDefinitionsApi).create_property_definition(
            create_property_definition_request=prop_def_req
        )
    except ApiException:
        print(f"Property definition {domain}/{scope}/{code} already exists.")


# ###### Setup API and portfolio name
scope = "test_portfolio_with_shks_as_cash"
portfolio_code = "test_portfolio_with_shks_as_cash"

api_factory = lusid.utilities.ApiClientFactory(
    app_name="commissions-script",
    api_secrets_filename=os.getenv("FBN_SECRETS_PATH")
)
transaction_portfolios_api = api_factory.build(lusid.api.TransactionPortfoliosApi)

# ###### CREATE PROPERTIES
# Could create more underlyingInstrumentId properties if desired.
# Eg UnderlyingInstrumentRIC, or UnderlyingInstrumentLUID etc...
property_scope = "test-scope-commissions"
transaction_underlying_instrument_id_property_key = f"Transaction/{property_scope}/UnderlyingInstrumentId"
transaction_commission_type_property_key = f"Transaction/{property_scope}/CommissionType"
instrument_some_property_on_an_instrument = f"Instrument/{property_scope}/SomeInstrumentProperty"
"""
Optional: When booking a transaction with cash,
then we need to create the same property in the 'Transaction' domain 
if we want to group commissions by instrument properties
"""
transaction_some_property_on_an_instrument = f"Transaction/{property_scope}/SomeInstrumentProperty"


check_or_create_property(api_factory, transaction_underlying_instrument_id_property_key)
check_or_create_property(api_factory, transaction_commission_type_property_key)
check_or_create_property(api_factory, instrument_some_property_on_an_instrument)
# Also create the instrument property for the transaction domain to allow us to group commission transactions/holdings
check_or_create_property(api_factory, transaction_some_property_on_an_instrument)

# ####### SETUP RELEVANT INSTRUMENTS FOR BOOKING COMMISSION TRANSACTIONS
instrument_1_identifier = "comms-test-inst1"
instrument_2_identifier = "comms-test-inst2"
some_instrument_property_value_1 = "instrument-property-value1"
some_instrument_property_value_2 = "instrument-property-test-value2"
setup_instruments(
    lusid_api_factory=api_factory, instrument_name=instrument_1_identifier,
    instrument_client_internal=instrument_1_identifier,
    properties=[property_def(instrument_some_property_on_an_instrument, some_instrument_property_value_1)]
)
setup_instruments(
    lusid_api_factory=api_factory, instrument_name=instrument_2_identifier,
    instrument_client_internal=instrument_2_identifier,
    properties=[property_def(instrument_some_property_on_an_instrument, some_instrument_property_value_2)]
)

# ####### Create portfolio with properties as sub-holding keys
subholding_keys = [
    transaction_underlying_instrument_id_property_key,
    transaction_commission_type_property_key,
    # Optional: Add the instrument property we created for the transaction domain
    # to allow grouping by instrument properties in the 'holdings' view
    transaction_some_property_on_an_instrument
]
portfolio_request = models.CreateTransactionPortfolioRequest(
    display_name="Test commission portfolio",
    code=portfolio_code,
    base_currency="GBP",
    created="2010-01-01T00:00:00.000000+00:00",
    sub_holding_keys=subholding_keys
)

try:
    create_portfolio_response = transaction_portfolios_api.create_portfolio(
        scope=scope, create_transaction_portfolio_request=portfolio_request
    )
    print("Portfolio created")
    print(f"Response: {create_portfolio_response}")
# Error will be thrown if the portfolio already exists
except ApiException as e:
    print(json.loads(e.body))

# ###### Configure commission transaction type
system_configuration_api = api_factory.build(lusid.api.SystemConfigurationApi)

# The following transaction type will always deduct cash from our holdings when booking transactions with this txn type
commission_transaction_type_alias = "Commission"
transaction_config_request = models.TransactionConfigurationDataRequest(
    aliases=[
        models.TransactionConfigurationTypeAlias(
            type=commission_transaction_type_alias,
            description="Commission transaction type",
            transaction_class="Basic",
            transaction_group="default",
            transaction_roles="AllRoles",
        )
    ],
    movements=[
        # This is the definition that causes cash (side2) to be deducted (direction=-1) on transaction booking
        # regardless of whether the transaction is booked as cash or with the underlying instrument
        models.TransactionConfigurationMovementDataRequest(
            movement_types="CashCommitment",
            side="Side2",
            direction=-1,
            properties={},
            # Optional: we can automatically assign property values when booking with this transaction type
            # for example:
            # mappings = [models.TransactionPropertyMappingRequest(
            #     property_key=f"Transaction/{scope}/CommissionType",
            #     set_to="BrokerCommission"
            # )]
            mappings=[],
        )
    ]
)
try:
    response = system_configuration_api.create_configuration_transaction_type(
        transaction_configuration_data_request=transaction_config_request
    )
    print("Transaction type created")
    print(f"response: {response}")
# Error will be thrown if the transaction type already exists
except ApiException as e:
    print(json.loads(e.body))

# ###### Add transactions
"""
Mind that below we are booking the commission transactions with a cash instrument. As a result, if we later want group these
transactions by the relevant underlying instrument properties, we need to append these properties to the transaction requests.
(Optionally we can also automate this step by calling the 'ListInstruments' API for the relevant underlying instrument id,
query the properties on that instrument, and append them to the transactions below)

We can also avoid this step if we instead decide to book the transaction with the underlying instrument identifier.
That way, we will still create cash holdings because of our 'Commission' transaction type (which has a negative cash movement direction), 
and instrument properties will be automatically available on the transactions. 
(Although we will still have to create sub-holding key property in the transaction domain to group our holdings)
"""
transaction_requests = []
transaction_request1 = models.TransactionRequest(
    transaction_id="your_transaction_id",
    type=commission_transaction_type_alias,
    instrument_identifiers={f"Instrument/default/Currency": "GBP"},
    transaction_date="2010-01-01T00:00:00.000000+00:00",
    settlement_date="2010-01-01T00:00:00.000000+00:00",
    units=100,
    transaction_currency="GBP",
    total_consideration=models.CurrencyAndAmount(
        amount=100, currency="GBP"
    ),
    counterparty_id="some_cp_id",
    properties={
        transaction_underlying_instrument_id_property_key: models.PerpetualProperty(
            key=transaction_underlying_instrument_id_property_key,
            value=models.PropertyValue(label_value=instrument_1_identifier)
        ),
        transaction_commission_type_property_key: models.PerpetualProperty(
            key=transaction_commission_type_property_key,
            value=models.PropertyValue(label_value="BrokerCommission")
        ),
        # Optional addition of instrument property value, but in the 'Transaction' domain
        transaction_some_property_on_an_instrument: models.PerpetualProperty(
            key=transaction_some_property_on_an_instrument,
            value=models.PropertyValue(label_value=some_instrument_property_value_1)
        ),

    },
)
transaction_request2 = models.TransactionRequest(
    transaction_id="your_transaction_id2",
    type=commission_transaction_type_alias,
    instrument_identifiers={f"Instrument/default/Currency": "GBP"},
    transaction_date="2010-01-01T00:00:00.000000+00:00",
    settlement_date="2010-01-01T00:00:00.000000+00:00",
    units=50,
    transaction_currency="GBP",
    total_consideration=models.CurrencyAndAmount(
        amount=50, currency="GBP"
    ),
    counterparty_id="some_cp_id",
    properties={
        transaction_underlying_instrument_id_property_key: models.PerpetualProperty(
            key=transaction_underlying_instrument_id_property_key,
            value=models.PropertyValue(label_value=instrument_2_identifier)
        ),
        transaction_commission_type_property_key: models.PerpetualProperty(
            transaction_commission_type_property_key,
            value=models.PropertyValue(label_value="ExchangeCommission")
        ),
        # Optional addition of instrument property value, but in the 'Transaction' domain
        transaction_some_property_on_an_instrument: models.PerpetualProperty(
            key=transaction_some_property_on_an_instrument,
            value=models.PropertyValue(label_value=some_instrument_property_value_2)
        )
    },
)

transaction_requests.append(transaction_request1)
transaction_requests.append(transaction_request2)

transaction_upsert_response = transaction_portfolios_api.upsert_transactions(
    scope=scope, code=portfolio_code, transaction_request=transaction_requests
)
print(transaction_upsert_response)

# Now we can view our transactions, as well as holdings,
# and group/filter them all by any instrument id, by any commission type,
# and by any property on the instrument that we appended to our transaction
