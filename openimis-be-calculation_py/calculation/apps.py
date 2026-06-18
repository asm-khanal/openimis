import importlib
import inspect

from django.apps import AppConfig
from core.abs_calculation_rule import AbsStrategy

MODULE_NAME = "calculation"


DEFAULT_CFG = {
    "gql_query_calculation_rule_perms": ["153001"],
    "gql_mutation_update_calculation_rule_perms": ["153003"],
}


CALCULATION_RULES = []


def read_all_calculation_rules(module_name, rule_list):
    calc_root = f"{module_name}.calculation_rule"
    """function to read all calculation rules from that module"""
    for name, cls in inspect.getmembers(importlib.import_module(calc_root), inspect.isclass):
        if issubclass(cls, AbsStrategy) and cls.__module__.startswith(calc_root):
            rule_list.append(cls)
            cls.ready()

class CalculationConfig(AppConfig):
    name = MODULE_NAME

    gql_query_calculation_rule_perms = []
    gql_mutation_update_calculation_rule_perms = []

    def __load_config(self, cfg):
        for field in cfg:
            if hasattr(CalculationConfig, field):
                setattr(CalculationConfig, field, cfg[field])

    def ready(self):
        from core.models import ModuleConfiguration
        cfg = ModuleConfiguration.get_or_default(MODULE_NAME, DEFAULT_CFG)
        self.__load_config(cfg)
        read_all_calculation_rules(MODULE_NAME, CALCULATION_RULES)
