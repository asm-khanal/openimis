import logging

from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.core.exceptions import PermissionDenied, ValidationError
from django.utils.translation import gettext as _

from .models import (
    HospitalPaymentBatch,
    HospitalPaymentBatchClaim,
    HospitalPaymentRecord,
)
from .serializers import (
    HospitalPaymentBatchSerializer,
    HospitalPaymentBatchClaimSerializer,
    HospitalPaymentRecordSerializer,
    ApprovePaymentBatchSerializer,
    PaymentWebhookSerializer,
)
from .services import (
    create_payment_batches,
    approve_payment_batch,
    process_webhook_payment_confirmation,
)
from .apps import HospitalPaymentConfig

logger = logging.getLogger(__name__)


class PaymentBatchListView(generics.ListCreateAPIView):
    """
    GET: List all hospital payment batches with their claims (bulk view).
    POST: Create new payment batches from valuated claims.

    Shows all claims of each hospital collected in bulk when a certain amount is reached.
    """
    serializer_class = HospitalPaymentBatchSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = HospitalPaymentBatch.objects.filter(
            validity_to__isnull=True
        ).select_related("health_facility", "approved_by")

        # Filter by status if provided
        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Filter by health facility if provided
        hf_filter = self.request.query_params.get("health_facility")
        if hf_filter:
            queryset = queryset.filter(health_facility_id=hf_filter)

        return queryset.order_by("-validity_from")

    def create(self, request, *args, **kwargs):
        if not request.user.has_perms(
            HospitalPaymentConfig.rest_view_payment_batches_perms
        ):
            raise PermissionDenied(_("unauthorized"))

        health_facility_ids = request.data.get("health_facility_ids")
        batches = create_payment_batches(request.user, health_facility_ids)

        if not batches:
            return Response(
                {"detail": _("No valuated claims available for batch creation.")},
                status=status.HTTP_200_OK,
            )

        serializer = self.get_serializer(batches, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class PaymentBatchDetailView(generics.RetrieveAPIView):
    """
    GET: Detail of a specific payment batch including all claims.
    """
    serializer_class = HospitalPaymentBatchSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return HospitalPaymentBatch.objects.filter(
            validity_to__isnull=True
        ).select_related("health_facility", "approved_by")


class ApprovePaymentBatchView(APIView):
    """
    POST: Admin approves payment batches for processing.
    After approval, the payment API is called automatically via Celery task.

    Request body:
    {
        "batch_ids": [1, 2, 3]
    }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        if not request.user.has_perms(
            HospitalPaymentConfig.rest_approve_payment_batch_perms
        ):
            raise PermissionDenied(_("unauthorized"))

        serializer = ApprovePaymentBatchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        batch_ids = serializer.validated_data["batch_ids"]
        approved_batches = approve_payment_batch(request.user, batch_ids)

        # Trigger async payment processing for each approved batch
        from .tasks import process_payment_batch_task
        for batch in approved_batches:
            process_payment_batch_task.delay(batch.id)

        result_serializer = HospitalPaymentBatchSerializer(approved_batches, many=True)
        return Response(
            {
                "detail": _(f"{len(approved_batches)} batch(es) approved. "
                           "Payment processing initiated."),
                "batches": result_serializer.data,
            },
            status=status.HTTP_200_OK,
        )


class PaymentWebhookView(APIView):
    """
    POST: Receives payment confirmation from the external payment API.
    This endpoint is called by the payment API without human intervention.

    The payment API sends JSON of what has been paid (or if all has been paid).
    After receiving the response, the payment details are stored automatically.

    Request body:
    {
        "batch_reference": "HPB-HF001-20260618...",
        "payment_reference": "PAY-12345",
        "status": "PAID",
        "total_paid_amount": 50000.00,
        "claims_paid": [101, 102, 103],
        "claims_failed": [],
        "raw_response": {...}
    }
    """
    # No authentication required - webhook is called by external payment API
    # Authentication is handled via API key in headers (configured in settings)
    permission_classes = []
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        serializer = PaymentWebhookSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            batch = process_webhook_payment_confirmation(
                serializer.validated_data
            )
            result_serializer = HospitalPaymentBatchSerializer(batch)
            return Response(
                {
                    "detail": _("Payment confirmation processed successfully."),
                    "batch": result_serializer.data,
                },
                status=status.HTTP_200_OK,
            )
        except ValueError as e:
            logger.error(f"Webhook payment confirmation error: {e}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            logger.error(f"Webhook payment confirmation error: {e}", exc_info=True)
            return Response(
                {"error": _("Internal server error processing payment confirmation.")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class PaymentRecordListView(generics.ListAPIView):
    """
    GET: List all payment records (responses from payment API).
    """
    serializer_class = HospitalPaymentRecordSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = HospitalPaymentRecord.objects.filter(
            validity_to__isnull=True
        ).select_related("payment_batch")

        batch_id = self.request.query_params.get("payment_batch")
        if batch_id:
            queryset = queryset.filter(payment_batch_id=batch_id)

        return queryset.order_by("-received_date")
