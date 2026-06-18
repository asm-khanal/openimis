# openIMIS Backend Calculation reference module
This repository holds the files of the openIMIS Backend Calculation reference module.
It is dedicated to be deployed as a module of [openimis-be_py](https://github.com/openimis/openimis-be_py).

## Models
  - None (using no database approach for CalculationRule) - Calculation Rule is saved by defining class 
    extending the ABSCalculationClass from core module.

## Listened Django Signals
  - signal_get_rule_name
  - signal_get_rule_details
  - signal_get_param
  - signal_get_linked_class
  - signal_calculate_event

## GraphQl Queries
* calculationRules
  - allow frontend to fetch the all calculation rules data
* calculationRulesByClassName 
  - allow frontend to fetch the calculation data based on its name 
* calculationParams
  - allow frontend to fetch the calculation parameters
* linkedClass
  - allow frontend to fetch the linked class related to chosen instance

## Services
  - get_rule_name(class_name)
    - return the names of calculation rules
  - get_rule_details(class_name)
    - this function will send a signal and the rules will reply if they have 
      object matching the classname in their list of object 
  - run_calculation_rules(instance, context, user) 
    - trigger calculations so as to calculate based on provided parameters
  - get_parameters(class_name, instance)
    - return the ruleDetails that are valid to classname and related to instance
  - get_linked_class(class_name_list)
    - List[ClassName] is send from FE, by checking the class used in page where the user 
      have access
    - return all the ListClass

## Configuration options (can be changed via core.ModuleConfiguration)
* gql_query_calculation_rule_perms: required rights to call all graphQl queries defined for Calculation module (default: ["153001"])
* gql_mutation_update_calculation_rule_perms: required rights to update CalculationRule (default: ["153003"])
