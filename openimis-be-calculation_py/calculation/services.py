from .apps import CALCULATION_RULES
from uuid import UUID


def get_rule_name(class_name):
    list_rule_name = []
    for calculation_rule in CALCULATION_RULES:
        result_signal = calculation_rule.get_rule_name(sender=class_name, class_name=class_name)
        if result_signal:
            list_rule_name.append(result_signal)
    return list_rule_name


def get_rule_details(class_name):
    dict_rule_details = {}
    for calculation_rule in CALCULATION_RULES:
        result_signal = calculation_rule.get_rule_details(sender=class_name, class_name=class_name)
        if result_signal and 'parameters' in result_signal:
            if class_name not in dict_rule_details:
                dict_rule_details[class_name] = result_signal['parameters']
            else:
                to_update = [
                    p for p in result_signal['parameters']
                    if all([p['name'] != sp['name'] for sp in dict_rule_details[class_name]])
                ]
                dict_rule_details[class_name] += to_update
    return dict_rule_details


def get_calculation_object(uuid):
    for calculation_rule in CALCULATION_RULES:
        if UUID(str(calculation_rule.uuid)) == UUID(str(uuid)):
            return calculation_rule


def run_calculation_rules(instance, context, user, **kwargs):
    for calculation_rule in CALCULATION_RULES:
        result = calculation_rule.run_calculation_rules(
            sender=instance.__class__.__name__, instance=instance, user=user, context=context, **kwargs
        )
        if result:
            return result

    # if no listened calculation rules - return None
    return None


def get_parameters(class_name, instance):
    """ className is the class name of the object where the calculation param need to be added
        instance is where the link with a calculation need to be found,
         like the CPB in case of PH insuree or Contract Details
    """
    list_parameters = []
    for calculation_rule in CALCULATION_RULES:
        result_signal = calculation_rule.get_parameters(
            sender=instance, class_name=class_name, instance=instance
        )
        if result_signal:
            list_parameters.extend(result_signal)
    # return the ruleDetails that are valid to classname and related to instance
    return list_parameters


def get_linked_class(class_name_list=None):
    return_list_class = set()
    for calculation_rule in CALCULATION_RULES:
        if class_name_list is None:
            result_signal = calculation_rule.get_linked_class(sender="None", class_name=None)
            if result_signal:
                return_list_class = return_list_class.union(set(result_signal))
        else:
            for class_name in class_name_list:
                result_signal = calculation_rule.get_linked_class(sender=class_name, class_name=class_name)
                if result_signal:
                    return_list_class = return_list_class.union(set(result_signal))
    return list(return_list_class)
