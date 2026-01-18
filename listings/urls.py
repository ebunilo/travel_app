from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserViewSet,
    ListingViewSet,
    BookingViewSet,
    InitiatePaymentView,
    VerifyPaymentView,
    ChapaWebhookView,
    PaymentCallbackView,
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'listings', ListingViewSet, basename='listing')
router.register(r'bookings', BookingViewSet, basename='booking')

urlpatterns = [
    path('api/', include(router.urls)),
    path('api/payments/initiate/', InitiatePaymentView.as_view(), name='payment-initiate'),
    path('api/payments/verify/', VerifyPaymentView.as_view(), name='payment-verify'),
    path('api/payments/chapa/webhook/', ChapaWebhookView.as_view(), name='payment-chapa-webhook'),
    path('payments/callback/', PaymentCallbackView.as_view(), name='payment-callback'),
]
