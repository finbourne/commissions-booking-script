import json
import logging
import os
import sys

import lusid
import lusid.models as models
from lusid import ApiException
from lusidtools.cocoon.transaction_type_upload import create_transaction_type_configuration


def check_or_create_property(api_factory, property_key):
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
        api_factory.build(lusid.api.PropertyDefinitionsApi).create_property_definition(
            create_property_definition_request=prop_def_req
        )
    except ApiException:
        logging.info(f"Property definition {domain}/{scope}/{code} already exists.")


def create_commission_txn_type(api_factory):
    create_transaction_type_configuration(
        api_factory,
        alias=models.TransactionConfigurationTypeAlias(
            type="Commission",
            description="Commission on transactions",
            transaction_class="Basic",
            transaction_group="default",
            transaction_roles="Longer"
        ),
        movements=[
            models.TransactionConfigurationMovementDataRequest(
                movement_types="CashCommitment",
                side="Side2",
                direction=-1,
                properties=None,
                mappings=None,
            )
        ],
    )


def get_commission_rate_from_lookup(country, broker, entity):
    config_file_path = os.getenv("FBN_COMMISSIONS_CONFIG_PATH")
    if not config_file_path:
        raise FileNotFoundError(f"The file {config_file_path} does not exist")

    with open(config_file_path, 'r') as json_file_contents:
        mapping = json_file_contents.read()
        mapping = json.loads(mapping)

    if len(mapping.keys()) == 0:
        raise ValueError(f"The no mapping config found in the {config_file_path} path")

    try:
        mapping[country][broker][entity]
    except KeyError:
        logging.info(f"The mapping file contents are: \n {mapping}\n")
        logging.info("One of the following values does not match the mapping config")
        logging.info(f"Country: {country}")
        logging.info(f"Broker: {broker}")
        logging.info(f"Entity: {entity}")
        # TODO: Need to decide whether to return value of 0 or error out when the broker, entity or country values are wrong
        return 0

    return mapping[country][broker][entity]


def setup_logging():
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.INFO)
    logging_formatter = logging.Formatter('%(levelname)s %(asctime)s - %(message)s')
    stdout_handler.setFormatter(logging_formatter)
    root_logger.addHandler(stdout_handler)
