import uuid

from contribution.models import Payer, Premium


def create_test_payer(payer_type=Payer.PAYER_TYPE_OTHER, custom_props=None):
    if custom_props is None:
        custom_props = {}
    else:
        custom_props = {k: v for k, v in custom_props.items() if hasattr(Payer, k)}
    payer = Payer.objects.create(
        **{
            "type": payer_type,
            "uuid": uuid.uuid4(),
            "name": "Test Default Payer Name",
            "address": "Test street name 123, CZ9204 City, Country",
            "validity_from": "2019-01-01",
            "audit_user_id": -1,
            **custom_props
        }
    )
    return payer
