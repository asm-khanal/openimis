import graphene
from django.db.models import Q
from django.core.exceptions import PermissionDenied
import graphene_django_optimizer as gql_optimizer
from core import filter_validity
from django.utils.translation import gettext as _, gettext_lazy
from payer.apps import PayerConfig
from core.schema import OrderedDjangoFilterConnectionField
from .models import Payer
from location.models import Location, LocationManager
from product.schema import ProductGQLType

from .gql_queries import PayerGQLType, FundingGQLType

from .gql_mutations import (
    CreatePayerMutation,
    UpdatePayerMutation,
    DeletePayerMutation,
    AddFundingMutation,
)


class Query(graphene.ObjectType):
    fundings = OrderedDjangoFilterConnectionField(
        FundingGQLType,
        payer_id=graphene.ID(),
        client_mutation_id=graphene.String(),
        show_history=graphene.Boolean(),
        parent_location_level=graphene.Int(),
        orderBy=graphene.List(of_type=graphene.String),
    )
    
    funding = graphene.Field(FundingGQLType, uuid=graphene.UUID())

        
    payers = OrderedDjangoFilterConnectionField(
        PayerGQLType,
        show_history=graphene.Boolean(),
        search=graphene.String(
            description=gettext_lazy("Search in `name`, `phone` & `email`")
        ),
        orderBy=graphene.List(of_type=graphene.String),
    )
    payer = graphene.Field(PayerGQLType, uuid=graphene.UUID())

    def resolve_payer(self, info, uuid, **kwargs):
        if not info.context.user.has_perms(PayerConfig.gql_query_payers_perms):
            raise PermissionDenied(_("unauthorized"))

        return Payer.objects.get(uuid=uuid)

    def resolve_payers(self, info, **kwargs):
        if not info.context.user.has_perms(PayerConfig.gql_query_payers_perms):
            raise PermissionDenied(_("unauthorized"))

        filters = Payer.objects
        show_history = kwargs.get("show_history", False)
        if not show_history:
            filters = filters.filter(*filter_validity(**kwargs))

        search = kwargs.get("search", None)
        if search is not None:
            filters = filters.filter(
                Q(name__icontains=search)
                | Q(phone__icontains=search)
                | Q(email__icontains=search)
            )

        filters = LocationManager().build_user_location_filter_query(info.context.user._u, queryset = filters)

        return gql_optimizer.query(filters, info)


class Mutation(graphene.ObjectType):
    create_payer = CreatePayerMutation.Field()
    update_payer = UpdatePayerMutation.Field()
    delete_payer = DeletePayerMutation.Field()
    add_funding = AddFundingMutation.Field()
