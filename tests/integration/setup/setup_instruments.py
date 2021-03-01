import lusid.models as models
import lusid


def setup_instruments(api_factory, instrument_name, instrument_client_internal, properties: list):

    # Create an instrument
    test_instrument_req1 = models.InstrumentDefinition(
        name=instrument_name,
        identifiers={"ClientInternal": models.InstrumentIdValue(value=instrument_client_internal)},
        properties=properties
    )
    api_factory.build(lusid.api.InstrumentsApi).upsert_instruments(
        request_body={"request1": test_instrument_req1}
    )