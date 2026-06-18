from django.test import TestCase, RequestFactory
from unittest.mock import Mock, patch, MagicMock
from graphene.test import Client
from graphene import Schema
from uuid import UUID
import json
from core.test_helpers import LogInHelper
from core.abs_calculation_rule import AbsStrategy
from core import datetime
from calculation.schema import Query
from calculation.apps import CALCULATION_RULES, CalculationConfig


class MockCalculationRule1(AbsStrategy):
    """Mock calculation rule for testing"""
    version = 1
    uuid = "11111111-1111-1111-1111-111111111111"
    calculation_rule_name = "Test Rule 1"
    description = "Test rule 1 description"
    impacted_class_parameter = []
    date_valid_from = datetime.datetime(2000, 1, 1)
    date_valid_to = None
    status = "active"
    from_to = [{"from": "ClassA", "to": "ClassB"}]
    type = "social_protection"
    sub_type = "benefit_plan"
    supports_advanced_criteria = True

    @classmethod
    def check_calculation(cls, instance):
        return True

    @classmethod
    def active_for_object(cls, instance, context, type=None, sub_type=None):
        return True

    @classmethod
    def calculate(cls, instance, *args, **kwargs):
        return {}

    @classmethod
    def convert(cls, instance, convert_to, **kwargs):
        return {}


class MockCalculationRule2(AbsStrategy):
    """Mock calculation rule for testing with different type"""
    version = 1
    uuid = "22222222-2222-2222-2222-222222222222"
    calculation_rule_name = "Test Rule 2"
    description = "Test rule 2 description"
    impacted_class_parameter = []
    date_valid_from = datetime.datetime(2000, 1, 1)
    date_valid_to = None
    status = "active"
    from_to = [{"from": "ClassC", "to": "ClassD"}]
    type = "account_payable"
    sub_type = "payment_plan"
    supports_advanced_criteria = False

    @classmethod
    def check_calculation(cls, instance):
        return True

    @classmethod
    def active_for_object(cls, instance, context, type=None, sub_type=None):
        return True

    @classmethod
    def calculate(cls, instance, *args, **kwargs):
        return {}

    @classmethod
    def convert(cls, instance, convert_to, **kwargs):
        return {}


class MockCalculationRule3(AbsStrategy):
    """Mock calculation rule for testing with account_receivable type"""
    version = 1
    uuid = "33333333-3333-3333-3333-333333333333"
    calculation_rule_name = "Test Rule 3"
    description = "Test rule 3 description"
    impacted_class_parameter = []
    date_valid_from = datetime.datetime(2000, 1, 1)
    date_valid_to = None
    status = "inactive"
    from_to = []
    type = "account_receivable"
    sub_type = "contribution"
    supports_advanced_criteria = True

    @classmethod
    def check_calculation(cls, instance):
        return True

    @classmethod
    def active_for_object(cls, instance, context, type=None, sub_type=None):
        return True

    @classmethod
    def calculate(cls, instance, *args, **kwargs):
        return {}

    @classmethod
    def convert(cls, instance, convert_to, **kwargs):
        return {}


class CalculationRulesQueryTest(TestCase):
    """Test the calculation_rules GraphQL query"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = LogInHelper().get_or_create_user_api()
        cls.schema = Schema(query=Query)

        cls.original_calculation_rules = CALCULATION_RULES.copy()
        CALCULATION_RULES.clear()
        CALCULATION_RULES.extend([
            MockCalculationRule1,
            MockCalculationRule2,
            MockCalculationRule3
        ])

    @classmethod
    def tearDownClass(cls):
        CALCULATION_RULES.clear()
        CALCULATION_RULES.extend(cls.original_calculation_rules)
        super().tearDownClass()

    def setUp(self):
        self.client = Client(self.schema)
        self.factory = RequestFactory()

    def _get_graphql_context(self, has_perms=True):
        """Helper to create GraphQL context with proper permission setup"""
        request = self.factory.get('/graphql')
        request.user = self.user
        request.user.has_perms = Mock(return_value=has_perms)
        return request

    def test_calculation_rules_query_all_rules(self):
        """Test querying all calculation rules without filters"""
        query = '''
            query {
                calculationRules {
                    calculationRules {
                        uuid
                    }
                }
            }
        '''

        context = self._get_graphql_context()
        result = self.client.execute(query, context=context)

        self.assertIsNone(result.get('errors'))
        self.assertIn('data', result)

        rules = result['data']['calculationRules']['calculationRules']
        self.assertEqual(len(rules), 3)

        uuids = [rule['uuid'] for rule in rules]
        self.assertIn("11111111-1111-1111-1111-111111111111", uuids)
        self.assertIn("22222222-2222-2222-2222-222222222222", uuids)
        self.assertIn("33333333-3333-3333-3333-333333333333", uuids)

    def test_calculation_rules_query_by_uuid(self):
        """Test querying calculation rules by specific UUID"""
        query = '''
            query {
                calculationRules(calculation: "11111111-1111-1111-1111-111111111111") {
                    calculationRules {
                        uuid
                        calculationClassName
                        status
                        description
                        type
                        subType
                        fromTo
                        supportsAdvancedCriteria
                    }
                }
            }
        '''

        context = self._get_graphql_context()
        result = self.client.execute(query, context=context)

        self.assertIsNone(result.get('errors'))
        rules = result['data']['calculationRules']['calculationRules']
        self.assertEqual(len(rules), 1)
        rule = rules[0]

        self.assertEqual(rule['uuid'], "11111111-1111-1111-1111-111111111111")
        self.assertEqual(rule['calculationClassName'], "Test Rule 1")
        self.assertEqual(rule['status'], "active")
        self.assertEqual(rule['type'], "social_protection")
        self.assertEqual(rule['subType'], "benefit_plan")

        self.assertIsNotNone(rule['fromTo'])
        from_to = json.loads(rule['fromTo'])
        self.assertEqual(from_to, [{"from": "ClassA", "to": "ClassB"}])

        self.assertTrue(rule['supportsAdvancedCriteria'])

    def test_calculation_rules_query_by_type(self):
        """Test querying calculation rules by type"""
        query = '''
            query {
                calculationRules(calcruleType: "social_protection") {
                    calculationRules {
                        uuid
                        calculationClassName
                        type
                    }
                }
            }
        '''

        context = self._get_graphql_context()
        result = self.client.execute(query, context=context)

        self.assertIsNone(result.get('errors'))
        rules = result['data']['calculationRules']['calculationRules']
        self.assertEqual(len(rules), 1)
        self.assertEqual(rules[0]['type'], "social_protection")
        self.assertEqual(rules[0]['calculationClassName'], "Test Rule 1")

        query = '''
            query {
                calculationRules(calcruleType: "account_receivable") {
                    calculationRules {
                        uuid
                        calculationClassName
                        type
                        status
                    }
                }
            }
        '''

        context = self._get_graphql_context()
        result = self.client.execute(query, context=context)

        self.assertIsNone(result.get('errors'))
        rules = result['data']['calculationRules']['calculationRules']
        self.assertEqual(len(rules), 1)
        self.assertEqual(rules[0]['type'], "account_receivable")
        self.assertEqual(rules[0]['calculationClassName'], "Test Rule 3")
        self.assertEqual(rules[0]['status'], "inactive")

    def test_calculation_rules_query_by_uuid_and_type_matching(self):
        """Test querying by UUID and type when both match"""
        query = '''
            query {
                calculationRules(
                    calculation: "11111111-1111-1111-1111-111111111111",
                    calcruleType: "social_protection"
                ) {
                    calculationRules {
                        uuid
                        type
                    }
                }
            }
        '''

        context = self._get_graphql_context()
        result = self.client.execute(query, context=context)

        self.assertIsNone(result.get('errors'))
        rules = result['data']['calculationRules']['calculationRules']
        self.assertEqual(len(rules), 1)
        self.assertEqual(rules[0]['uuid'], "11111111-1111-1111-1111-111111111111")
        self.assertEqual(rules[0]['type'], "social_protection")

    def test_calculation_rules_query_by_uuid_and_type_not_matching(self):
        """Test querying by UUID and type when type doesn't match"""
        query = '''
            query {
                calculationRules(
                    calculation: "11111111-1111-1111-1111-111111111111",
                    calcruleType: "account_payable"
                ) {
                    calculationRules {
                        uuid
                    }
                }
            }
        '''

        context = self._get_graphql_context()
        result = self.client.execute(query, context=context)

        self.assertIsNone(result.get('errors'))
        rules = result['data']['calculationRules']['calculationRules']
        self.assertEqual(len(rules), 0)

    def test_calculation_rules_query_nonexistent_uuid(self):
        """Test querying with non-existent UUID"""
        query = '''
            query {
                calculationRules(calculation: "99999999-9999-9999-9999-999999999999") {
                    calculationRules {
                        uuid
                    }
                }
            }
        '''

        context = self._get_graphql_context()
        result = self.client.execute(query, context=context)

        self.assertIsNone(result.get('errors'))
        rules = result['data']['calculationRules']['calculationRules']
        self.assertEqual(len(rules), 0)

    def test_calculation_rules_query_nonexistent_type(self):
        """Test querying with non-existent type"""
        query = '''
            query {
                calculationRules(calcruleType: "nonexistent_type") {
                    calculationRules {
                        uuid
                    }
                }
            }
        '''

        context = self._get_graphql_context()
        result = self.client.execute(query, context=context)

        self.assertIsNone(result.get('errors'))
        rules = result['data']['calculationRules']['calculationRules']
        self.assertEqual(len(rules), 0)

    def test_calculation_rules_query_without_permission(self):
        """Test that query raises PermissionError without proper permissions"""
        query = '''
            query {
                calculationRules {
                    calculationRules {
                        uuid
                    }
                }
            }
        '''

        context = self._get_graphql_context(has_perms=False)
        result = self.client.execute(query, context=context)

        self.assertIsNotNone(result.get('errors'))
        self.assertIn('Unauthorized', str(result['errors'][0]))

    def test_calculation_rules_empty_from_to(self):
        """Test calculation rule with empty from_to"""
        query = '''
            query {
                calculationRules(calculation: "33333333-3333-3333-3333-333333333333") {
                    calculationRules {
                        fromTo
                    }
                }
            }
        '''

        context = self._get_graphql_context()
        result = self.client.execute(query, context=context)

        self.assertIsNone(result.get('errors'))
        rules = result['data']['calculationRules']['calculationRules']
        from_to = json.loads(rules[0]['fromTo'])
        self.assertEqual(from_to, [])

