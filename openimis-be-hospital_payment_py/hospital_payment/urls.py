from django.urls import path

from .views import (
    PaymentBatchListView,
    PaymentBatchDetailView,
    ApprovePaymentBatchView,
    PaymentWebhookView,
    PaymentRecordListView,
)

urlpatterns = [
    path("", PaymentBatchListView.as_view(), name="payment_batches"),
    path("<int:pk>/", PaymentBatchDetailView.as_view(), name="payment_batch_detail"),
    path("approve/", ApprovePaymentBatchView.as_view(), name="approve_payment_batch"),
    path("webhook/", PaymentWebhookView.as_view(), name="payment_webhook"),
    path("records/", PaymentRecordListView.as_view(), name="payment_records"),
]
