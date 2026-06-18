
import graphene
import logging
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext as _

from core.schema import OpenIMISMutation
from .apps import HospitalPaymentConfig
from .models import (
    HospitalPaymentBatch,
    HospitalPaymentBatchClaim,
    HospitalPaymentRecord,
)
from .services import (
    create_payment_batches,
    approve_payment_batch,
)

logger = logging.getLogger(__name__)


class HospitalPaymentBatchGQLType(DjangoObjectType):
    class Meta:
        model = HospitalPaymentBatch
        interfaces = (graphene.relay.Node,)
        filter_fields = {
            "id": ["exact"],
            "uuid": ["exact"],
            "batch_code": ["exact", "icontains"],
            "health_facility__id": ["exact"],
            "health_facility__code": ["exact"],
            "status": ["exact"],
        }



class HospitalPaymentBatchClaimGQLType(DjangoObjectType):
    class Meta:
        model = HospitalPaymentBatchClaim
        interfaces = (graphene.relay.Node,)
        filter_fields = {
            "id": ["exact"],
            "payment_batch__id": ["exact"],
            "claim__id": ["exact"],
            "status": ["exact"],
        }


class HospitalPaymentRecordGQLType(DjangoObjectType):
    class Meta:
        model = HospitalPaymentRecord
        interfaces = (graphene.relay.Node,)
        filter_fields = {
            "id": ["exact"],
            "uuid": ["exact"],
            "payment_batch__id": ["exact"],
            "status": ["exact"],
        }


class Query(graphene.ObjectType):
    hospital_payment_batches = DjangoFilterConnectionField(
        HospitalPaymentBatchGQLType,
        orderBy=graphene.List(of_type=graphene.String),
    )

    hospital_payment_batch = graphene.Field(
        HospitalPaymentBatchGQLType,
        id=graphene.Int(),
        uuid=graphene.String(),
    )

    hospital_payment_records = DjangoFilterConnectionField(
        HospitalPaymentRecordGQLType
    )

    def resolve_hospital_payment_batches(self, info, **kwargs):
        if not info.context.user.has_perms(
            HospitalPaymentConfig.gql_query_hospital_payment_batches_perms
        ):
            raise PermissionDenied(_("unauthorized"))
        queryset = HospitalPaymentBatch.objects.filter(validity_to__isnull=True)
        return queryset

    def resolve_hospital_payment_batch(self, info, **kwargs):
        if not info.context.user.has_perms(
            HospitalPaymentConfig.gql_query_hospital_payment_batches_perms
        ):
            raise PermissionDenied(_("unauthorized"))
        id = kwargs.get("id")
        uuid = kwargs.get("uuid")
        if id:
            return HospitalPaymentBatch.objects.filter(
                id=id, validity_to__isnull=True
            ).first()
        elif uuid:
            return HospitalPaymentBatch.objects.filter(
                uuid=uuid, validity_to__isnull=True
            ).first()
        return None

    def resolve_hospital_payment_records(self, info, **kwargs):
        if not info.context.user.has_perms(
            HospitalPaymentConfig.gql_query_hospital_payment_records_perms
        ):
            raise PermissionDenied(_("unauthorized"))
        return HospitalPaymentRecord.objects.filter(validity_to__isnull=True)


class CreateHospitalPaymentBatchMutation(OpenIMISMutation):
    """
    Create payment batches from valuated claims.
    Groups STATUS_VALUATED claims by health facility into bulk payment batches.
    """

    _mutation_module = "hospital_payment"
    _mutation_class = "CreateHospitalPaymentBatchMutation"

    class Input(OpenIMISMutation.Input):
        health_facility_ids = graphene.List(graphene.Int, required=False)

    @classmethod
    def async_mutate(cls, user, **data):
        if not user.has_perms(
            HospitalPaymentConfig.gql_mutation_create_hospital_payment_batch_perms
        ):
            raise PermissionDenied(_("unauthorized"))

        health_facility_ids = data.get("health_facility_ids")
        batches = create_payment_batches(user, health_facility_ids)

        if not batches:
            return None

        return None


class ApproveHospitalPaymentBatchMutation(OpenIMISMutation):
    """
    Approve payment batches for processing.
    After approval, payment is sent to the external payment API automatically.
    """

    _mutation_module = "hospital_payment"
    _mutation_class = "ApproveHospitalPaymentBatchMutation"

    class Input(OpenIMISMutation.Input):
        batch_ids = graphene.List(graphene.Int, required=True)

    @classmethod
    def async_mutate(cls, user, **data):
        if not user.has_perms(
            HospitalPaymentConfig.gql_mutation_approve_hospital_payment_batch_perms
        ):
            raise PermissionDenied(_("unauthorized"))

        batch_ids = data.get("batch_ids", [])
        approved_batches = approve_payment_batch(user, batch_ids)

        # Trigger async payment processing
        from .tasks import process_payment_batch_task
        for batch in approved_batches:
            process_payment_batch_task.delay(batch.id)

        return None


class Mutation(graphene.ObjectType):
    create_hospital_payment_batch = CreateHospitalPaymentBatchMutation.Field()
    approve_hospital_payment_batch = ApproveHospitalPaymentBatchMutation.Field()


def bind_signals():
    """Bind GraphQL signals for hospital_payment module."""
    pass
