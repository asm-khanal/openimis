from django.apps import AppConfig

MODULE_NAME = "payment"

DEFAULT_CFG = {
    "gql_query_payments_perms": ["101401"],
    "gql_mutation_create_payments_perms": ["101402"],
    "gql_mutation_update_payments_perms": ["101403"],
    "gql_mutation_delete_payments_perms": ["101404"],
    "default_validations_disabled": False,
}


class PaymentConfig(AppConfig):
    name = MODULE_NAME

    gql_query_payments_perms = []
    gql_mutation_create_payments_perms = []
    gql_mutation_update_payments_perms = []
    gql_mutation_delete_payments_perms = []
    default_validations_disabled = None

    def __load_config(self, cfg):
        for field in cfg:
            if hasattr(PaymentConfig, field):
                setattr(PaymentConfig, field, cfg[field])

    def ready(self):
        from core.models import ModuleConfiguration
        cfg = ModuleConfiguration.get_or_default(MODULE_NAME, DEFAULT_CFG)
        self.__load_config(cfg)
