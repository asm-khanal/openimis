from django.urls import path
from .views import (
    ClaimListView, ClaimDetailView, valuate_claim_api,
    PaymentBatchListView, PaymentBatchDetailView,
    ApprovePaymentBatchView, PaymentWebhookView, PaymentRecordListView,
)

urlpatterns = [
    path("claims/", ClaimListView.as_view(), name="claim_list"),
    path("claims/<int:pk>/", ClaimDetailView.as_view(), name="claim_detail"),
    path("claims/<int:pk>/valuate/", valuate_claim_api, name="claim_valuate"),
    path("payment_batches/", PaymentBatchListView.as_view(), name="payment_batches"),
    path("payment_batches/<int:pk>/", PaymentBatchDetailView.as_view(), name="payment_batch_detail"),
    path("payment_batches/approve/", ApprovePaymentBatchView.as_view(), name="approve_payment_batch"),
    path("payment_batches/webhook/", PaymentWebhookView.as_view(), name="payment_webhook"),
    path("payment_records/", PaymentRecordListView.as_view(), name="payment_records"),
]
