import lusid.models as models


def property_def(full_property, label_value):
    prop = models.ModelProperty(
        key=full_property,
        value=models.PropertyValue(
            label_value=label_value
        )
    )

    return prop


