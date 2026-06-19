import logging
from decimal import Decimal

from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction
from django.utils import timezone

from claim_app.models import Claim, ClaimItem, ClaimService
from hospital_payment.models import HospitalPaymentBatch, HospitalPaymentBatchClaim, HospitalPaymentRecord
from location.models import HealthFacility
from insuree.models import Insuree
from medical.models import Diagnosis, Item, Service

from .serializers import (
    ClaimListSerializer, ClaimDetailSerializer, ClaimCreateSerializer,
    HospitalPaymentBatchListSerializer, HospitalPaymentBatchClaimSerializer,
    HospitalPaymentRecordSerializer, ApprovePaymentBatchSerializer,
    PaymentWebhookSerializer,
)
from .services import (
    valuate_claim, create_payment_batches, approve_payment_batch,
    process_payment_batch, process_webhook_payment_confirmation,
)

logger = logging.getLogger(__name__)


class ClaimListView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return ClaimListSerializer
        return ClaimCreateSerializer

    def get_queryset(self):
        qs = Claim.objects.select_related("health_facility", "insuree", "diagnosis")
        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)
        hf_filter = self.request.query_params.get("health_facility")
        if hf_filter:
            qs = qs.filter(health_facility__code=hf_filter)
        return qs.order_by("-created_at")

    def create(self, request, *args, **kwargs):
        serializer = ClaimCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        hf = HealthFacility.objects.filter(code=data["health_facility_code"]).first()
        if not hf:
            return Response({"error": f"Health facility '{data['health_facility_code']}' not found"}, status=status.HTTP_400_BAD_REQUEST)

        insuree = Insuree.objects.filter(chf_id=data["insuree_chf_id"]).first()
        if not insuree:
            return Response({"error": f"Insuree '{data['insuree_chf_id']}' not found"}, status=status.HTTP_400_BAD_REQUEST)

        diagnosis = None
        if data.get("diagnosis_code"):
            diagnosis = Diagnosis.objects.filter(code=data["diagnosis_code"]).first()

        with transaction.atomic():
            claim_count = Claim.objects.count() + 1
            code = f"CLM-{hf.code}-{timezone.now().strftime('%Y%m%d')}-{claim_count:05d}"

            claimed_total = Decimal(0)
            for item_data in data.get("items", []):
                qty = item_data.get("qty_claimed", 1)
                price = Decimal(str(item_data.get("price_claimed", 0)))
                claimed_total += price * qty
            for svc_data in data.get("services", []):
                qty = svc_data.get("qty_claimed", 1)
                price = Decimal(str(svc_data.get("price_claimed", 0)))
                claimed_total += price * qty

            claim = Claim.objects.create(
                code=code,
                insuree=insuree,
                health_facility=hf,
                diagnosis=diagnosis,
                date_from=data["date_from"],
                date_to=data.get("date_to"),
                status=Claim.STATUS_ENTERED,
                claimed=claimed_total,
                created_by=request.user if request.user.is_authenticated else None,
            )

            for item_data in data.get("items", []):
                item_obj = Item.objects.filter(code=item_data.get("item_code")).first()
                ClaimItem.objects.create(
                    claim=claim,
                    item=item_obj,
                    qty_claimed=item_data.get("qty_claimed", 1),
                    price_claimed=Decimal(str(item_data.get("price_claimed", 0))),
                )

            for svc_data in data.get("services", []):
                svc_obj = Service.objects.filter(code=svc_data.get("service_code")).first()
                ClaimService.objects.create(
                    claim=claim,
                    service=svc_obj,
                    qty_claimed=svc_data.get("qty_claimed", 1),
                    price_claimed=Decimal(str(svc_data.get("price_claimed", 0))),
                )

        return Response(ClaimDetailSerializer(claim).data, status=status.HTTP_201_CREATED)


class ClaimDetailView(generics.RetrieveAPIView):
    queryset = Claim.objects.select_related("health_facility", "insuree", "diagnosis").prefetch_related("items__item", "services__service")
    serializer_class = ClaimDetailSerializer
    permission_classes = [IsAuthenticated]


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def valuate_claim_api(request, pk):
    try:
        claim = Claim.objects.get(pk=pk, status=Claim.STATUS_ENTERED)
    except Claim.DoesNotExist:
        return Response({"error": "Claim not found or already processed"}, status=status.HTTP_404_NOT_FOUND)

    valuate_claim(claim)
    return Response(ClaimDetailSerializer(claim).data, status=status.HTTP_200_OK)


class PaymentBatchListView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        return HospitalPaymentBatchListSerializer

    def get_queryset(self):
        qs = HospitalPaymentBatch.objects.prefetch_related("batch_claims", "health_facility")
        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)
        hf_filter = self.request.query_params.get("health_facility")
        if hf_filter:
            qs = qs.filter(health_facility__code=hf_filter)
        return qs.order_by("-created_at")

    def create(self, request, *args, **kwargs):
        health_facility_codes = request.data.get("health_facility_codes")
        batches = create_payment_batches(request.user, health_facility_codes)
        if not batches:
            return Response({"detail": "No valuated claims available for batch creation."}, status=status.HTTP_200_OK)
        serializer = self.get_serializer(batches, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class PaymentBatchDetailView(generics.RetrieveAPIView):
    queryset = HospitalPaymentBatch.objects.prefetch_related("batch_claims", "health_facility")
    serializer_class = HospitalPaymentBatchListSerializer
    permission_classes = [IsAuthenticated]


class ApprovePaymentBatchView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = ApprovePaymentBatchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        batch_ids = serializer.validated_data["batch_ids"]
        approved_batches = approve_payment_batch(request.user, batch_ids)

        import threading
        for batch in approved_batches:
            t = threading.Thread(target=process_payment_batch, args=(batch.id,))
            t.start()

        result_serializer = HospitalPaymentBatchListSerializer(approved_batches, many=True)
        return Response({
            "detail": f"{len(approved_batches)} batch(es) approved. Payment processing initiated.",
            "batches": result_serializer.data,
        }, status=status.HTTP_200_OK)


class PaymentWebhookView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        serializer = PaymentWebhookSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            batch = process_webhook_payment_confirmation(serializer.validated_data)
            result_serializer = HospitalPaymentBatchListSerializer(batch)
            return Response({
                "detail": "Payment confirmation processed successfully.",
                "batch": result_serializer.data,
            }, status=status.HTTP_200_OK)
        except ValueError as e:
            logger.error(f"Webhook error: {e}")
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Webhook error: {e}", exc_info=True)
            return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PaymentRecordListView(generics.ListAPIView):
    serializer_class = HospitalPaymentRecordSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = HospitalPaymentRecord.objects.select_related("payment_batch")
        batch_id = self.request.query_params.get("payment_batch")
        if batch_id:
            qs = qs.filter(payment_batch_id=batch_id)
        return qs.order_by("-received_date")
