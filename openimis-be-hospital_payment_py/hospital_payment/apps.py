import logging
from django.apps import AppConfig

logger = logging.getLogger(__name__)

MODULE_NAME = "hospital_payment"

DEFAULT_CFG = {
    "gql_query_hospital_payment_batches_perms": ["131801"],
    "gql_query_hospital_payment_records_perms": ["131802"],
    "gql_mutation_create_hospital_payment_batch_perms": ["131803"],
    "gql_mutation_approve_hospital_payment_batch_perms": ["131804"],
    "rest_view_payment_batches_perms": ["131805"],
    "rest_approve_payment_batch_perms": ["131806"],
    "rest_payment_webhook_perms": [],
    "min_claims_per_batch": 1,
    "payment_api_url": "https://convolutional-intertwistingly-madge.ngrok-free.dev",
    "payment_api_key": "",
    "payment_api_timeout": 30,
}


class HospitalPaymentConfig(AppConfig):
    name = MODULE_NAME

    gql_query_hospital_payment_batches_perms = []
    gql_query_hospital_payment_records_perms = []
    gql_mutation_create_hospital_payment_batch_perms = []
    gql_mutation_approve_hospital_payment_batch_perms = []
    rest_view_payment_batches_perms = []
    rest_approve_payment_batch_perms = []
    rest_payment_webhook_perms = []
    min_claims_per_batch = 1
    payment_api_url = "https://convolutional-intertwistingly-madge.ngrok-free.dev"
    payment_api_key = ""
    payment_api_timeout = 30

    def __load_config(self, cfg):
        for field in cfg:
            if hasattr(HospitalPaymentConfig, field):
                setattr(HospitalPaymentConfig, field, cfg[field])

    def ready(self):
        from core.models import ModuleConfiguration
        cfg = ModuleConfiguration.get_or_default(MODULE_NAME, DEFAULT_CFG)
        self.__load_config(cfg)
