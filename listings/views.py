from django.shortcuts import render
from rest_framework import viewsets, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status as drf_status
from django.conf import settings
from django.views.generic import TemplateView
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth.models import User
import requests
import uuid

from .models import Listing, Booking, Payment
from .serializers import ListingSerializer, BookingSerializer, UserSerializer, UserCreateUpdateSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

# Try to import a Celery task for sending confirmation emails if available
try:
    from .tasks import send_payment_confirmation_email  # define in your app if not present
except Exception:
    send_payment_confirmation_email = None

# Create your views here.

class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for User management.
    
    List all users, create new users, retrieve specific user details,
    update user information, and delete users.
    """
    queryset = User.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return UserCreateUpdateSerializer
        return UserSerializer

    @swagger_auto_schema(
        operation_description="List all users",
        responses={200: UserSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        """
        Retrieve a list of all users.
        """
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Create a new user",
        request_body=UserCreateUpdateSerializer,
        responses={201: UserSerializer}
    )
    def create(self, request, *args, **kwargs):
        """
        Create a new user account.
        
        Required fields:
        - username: unique username
        - email: user email address
        - password: minimum 8 characters
        
        Optional fields:
        - first_name
        - last_name
        - is_active: default True
        """
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Retrieve a specific user by ID",
        responses={200: UserSerializer}
    )
    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve details of a specific user.
        """
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Update a user",
        request_body=UserCreateUpdateSerializer,
        responses={200: UserSerializer}
    )
    def update(self, request, *args, **kwargs):
        """
        Update user information.
        
        All fields are optional.
        Password will be hashed if provided.
        """
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Partially update a user",
        request_body=UserCreateUpdateSerializer,
        responses={200: UserSerializer}
    )
    def partial_update(self, request, *args, **kwargs):
        """
        Partially update user information (PATCH request).
        """
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Delete a user",
        responses={204: "User deleted successfully"}
    )
    def destroy(self, request, *args, **kwargs):
        """
        Delete a user account.
        """
        return super().destroy(request, *args, **kwargs)


class ListingViewSet(viewsets.ModelViewSet):
    queryset = Listing.objects.all()
    serializer_class = ListingSerializer
    permission_classes = [permissions.AllowAny]  # adjust as needed

class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = [permissions.AllowAny]  # adjust as needed

    def create(self, request, *args, **kwargs):
        # Create the booking first
        response = super().create(request, *args, **kwargs)
        if response.status_code not in (drf_status.HTTP_201_CREATED,):
            return response

        booking_id = response.data.get("id")
        # Derive payment fields
        amount = response.data.get("total_price")
        currency = request.data.get("currency", "ETB")
        # Pull email/name from request or related user
        email = request.data.get("email") or (self.get_queryset().model.guest.field.remote_field.model.objects.get(pk=response.data["guest"]).email if response.data.get("guest") else None)
        first_name = request.data.get("first_name", "")
        last_name = request.data.get("last_name", "")

        phone_number = request.data.get("phone_number", "")

        if not all([booking_id, amount, email]):
            # If we cannot initiate payment, just return booking with warning
            response.data["payment_initiation"] = {"status": "failed", "detail": "Missing data to initiate payment (booking_id/amount/email)."}
            return response

        # Initialize Chapa payment
        tx_ref = f"booking-{booking_id}-{uuid.uuid4().hex[:8]}"
        payload = {
            "amount": str(amount),
            "currency": currency,
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "phone_number": phone_number,
            "tx_ref": tx_ref,
            "return_url": request.data.get("return_url", ""),
            "callback_url": request.data.get("callback_url", ""),
            "customization": {
                "title": "Payment",
                "description": f"Payment for booking id {booking_id}",
            },
        }
        headers = {
            "Authorization": f"Bearer {getattr(settings, 'CHAPA_SECRET_KEY', '')}",
            "Content-Type": "application/json",
        }
        if not headers["Authorization"].strip():
            response.data["payment_initiation"] = {"status": "failed", "detail": "Chapa secret key not configured."}
            return response

        try:
            chapa_resp = requests.post("https://api.chapa.co/v1/transaction/initialize", json=payload, headers=headers, timeout=20)
            data = chapa_resp.json() if chapa_resp.headers.get("Content-Type", "").startswith("application/json") else {"status": "failed"}
        except requests.RequestException as e:
            response.data["payment_initiation"] = {"status": "failed", "detail": f"Payment initialization failed: {e}"}
            return response

        if data.get("status") != "success":
            response.data["payment_initiation"] = {"status": "failed", "detail": data.get("message", "Failed to initialize payment"), "data": data.get("data")}
            return response

        checkout_url = data.get("data", {}).get("checkout_url")
        try:
            booking = Booking.objects.get(pk=booking_id)
        except Booking.DoesNotExist:
            response.data["payment_initiation"] = {"status": "failed", "detail": "Booking not found after creation."}
            return response

        payment = Payment.objects.create(
            booking=booking,
            amount=amount,
            currency=currency,
            status=Payment.STATUS_PENDING,
            tx_ref=tx_ref,
            checkout_url=checkout_url,
            chapa_transaction_id=data.get("data", {}).get("id")
        )

        response.data["payment_initiation"] = {
            "status": "success",
            "checkout_url": checkout_url,
            "tx_ref": payment.tx_ref,
            "payment_id": payment.id,
        }
        return response

class InitiatePaymentView(APIView):
    permission_classes = [permissions.AllowAny]  # adjust as needed

    @swagger_auto_schema(
        operation_summary="Initiate payment via Chapa",
        operation_description="Create a pending Payment and receive a hosted checkout URL. Requires booking_id, amount, and email.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["booking_id", "amount", "email"],
            properties={
                "booking_id": openapi.Schema(type=openapi.TYPE_INTEGER, description="Existing booking ID"),
                "amount": openapi.Schema(type=openapi.TYPE_NUMBER, description="Amount to charge (decimal as string/number)"),
                "currency": openapi.Schema(type=openapi.TYPE_STRING, default="ETB", description="Currency code, e.g., ETB or USD"),
                "email": openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL, description="Payer email"),
                "first_name": openapi.Schema(type=openapi.TYPE_STRING, description="Payer first name"),
                "last_name": openapi.Schema(type=openapi.TYPE_STRING, description="Payer last name"),
                "phone_number": openapi.Schema(type=openapi.TYPE_STRING, description="Payer phone number"),
                "return_url": openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_URI, description="URL to redirect user after payment"),
                "callback_url": openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_URI, description="Webhook URL for payment status callbacks"),
            },
            example={
                "booking_id": 123,
                "amount": "1500.00",
                "currency": "ETB",
                "email": "guest@example.com",
                "first_name": "Jane",
                "last_name": "Doe",
                "phone_number": "+251900000000",
                "return_url": "https://yourapp.com/pay/return",
                "callback_url": "https://yourapp.com/api/payments/chapa/callback",
            },
        ),
        responses={
            200: openapi.Response(
                description="Payment initialized",
                examples={
                    "application/json": {
                        "message": "Hosted Link",
                        "status": "success",
                        "data": {
                            "checkout_url": "https://checkout.chapa.co/payment/xyz",
                            "tx_ref": "booking-123-abcd1234",
                            "payment_id": 45,
                        },
                    }
                },
            ),
            400: openapi.Response(description="Validation error or Chapa init failed"),
            404: openapi.Response(description="Booking not found"),
            500: openapi.Response(description="Server misconfiguration (missing CHAPA_SECRET_KEY)"),
            502: openapi.Response(description="Chapa unreachable"),
        },
        tags=["Payments"],
    )
    def post(self, request):
        booking_id = request.data.get("booking_id")
        amount = request.data.get("amount")
        currency = request.data.get("currency", "ETB")
        email = request.data.get("email")
        first_name = request.data.get("first_name", "")
        last_name = request.data.get("last_name", "")
        phone_number = request.data.get("phone_number", "")

        if not all([booking_id, amount, email]):
            return Response({"detail": "booking_id, amount, and email are required."}, status=drf_status.HTTP_400_BAD_REQUEST)

        try:
            booking = Booking.objects.get(pk=booking_id)
        except Booking.DoesNotExist:
            return Response({"detail": "Booking not found."}, status=drf_status.HTTP_404_NOT_FOUND)

        tx_ref = f"booking-{booking_id}-{uuid.uuid4().hex[:8]}"

        payload = {
            "amount": str(amount),
            "currency": currency,
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "phone_number": phone_number,
            "tx_ref": tx_ref,
            "return_url": request.data.get("return_url", ""),
            "callback_url": request.data.get("callback_url", ""),
            "customization": {
                "title": "Payment",
                "description": f"Payment for booking id {booking_id}",
            },
        }
        headers = {
            "Authorization": f"Bearer {getattr(settings, 'CHAPA_SECRET_KEY', '')}",
            "Content-Type": "application/json",
        }

        if not headers["Authorization"].strip():
            return Response({"detail": "Chapa secret key not configured."}, status=drf_status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            chapa_resp = requests.post("https://api.chapa.co/v1/transaction/initialize", json=payload, headers=headers, timeout=20)
        except requests.RequestException as e:
            return Response({"detail": f"Payment initialization failed: {e}"}, status=drf_status.HTTP_502_BAD_GATEWAY)

        data = chapa_resp.json() if chapa_resp.headers.get("Content-Type", "").startswith("application/json") else {"status": "failed"}
        if data.get("status") != "success":
            return Response({"detail": data.get("message", "Failed to initialize payment"), "data": data.get("data")}, status=drf_status.HTTP_400_BAD_REQUEST)

        checkout_url = data.get("data", {}).get("checkout_url")
        payment = Payment.objects.create(
            booking=booking,
            amount=amount,
            currency=currency,
            status=Payment.STATUS_PENDING,
            tx_ref=tx_ref,
            checkout_url=checkout_url,
            chapa_transaction_id=data.get("data", {}).get("id")  # if Chapa returns an id; may be None
        )

        return Response(
            {
                "message": "Hosted Link",
                "status": "success",
                "data": {
                    "checkout_url": checkout_url,
                    "tx_ref": payment.tx_ref,
                    "payment_id": payment.id,
                },
            },
            status=drf_status.HTTP_200_OK,
        )

class VerifyPaymentView(APIView):
    permission_classes = [permissions.AllowAny]  # adjust as needed

    @swagger_auto_schema(
        operation_summary="Verify payment via Chapa",
        operation_description="Verify a payment using its tx_ref. Updates Payment status and returns Chapa verification payload.",
        manual_parameters=[
            openapi.Parameter(
                name="tx_ref",
                in_=openapi.IN_QUERY,
                required=True,
                type=openapi.TYPE_STRING,
                description="Transaction reference returned during initiation",
            )
        ],
        responses={
            200: openapi.Response(
                description="Payment verified successfully",
                examples={
                    "application/json": {
                        "status": "success",
                        "payment_status": "completed",
                        "data": {
                            "tx_ref": "booking-123-abcd1234",
                            "amount": "1500.00",
                            "currency": "ETB",
                            "status": "success",
                            # ... other fields from Chapa ...
                        },
                    }
                },
            ),
            400: openapi.Response(description="Missing tx_ref or verification failed"),
            404: openapi.Response(description="Payment not found"),
            500: openapi.Response(description="Server misconfiguration (missing CHAPA_SECRET_KEY)"),
            502: openapi.Response(description="Chapa unreachable"),
        },
        tags=["Payments"],
    )
    def get(self, request):
        tx_ref = request.query_params.get("tx_ref")
        if not tx_ref:
            return Response({"detail": "tx_ref is required."}, status=drf_status.HTTP_400_BAD_REQUEST)

        try:
            payment = Payment.objects.get(tx_ref=tx_ref)
        except Payment.DoesNotExist:
            return Response({"detail": "Payment not found."}, status=drf_status.HTTP_404_NOT_FOUND)

        headers = {
            "Authorization": f"Bearer {getattr(settings, 'CHAPA_SECRET_KEY', '')}",
            "Content-Type": "application/json",
        }
        if not headers["Authorization"].strip():
            return Response({"detail": "Chapa secret key not configured."}, status=drf_status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Chapa verification typically uses /v1/transaction/verify/{tx_ref}
        url = f"https://api.chapa.co/v1/transaction/verify/{tx_ref}"
        try:
            chapa_resp = requests.get(url, headers=headers, timeout=20)
        except requests.RequestException as e:
            return Response({"detail": f"Verification failed: {e}"}, status=drf_status.HTTP_502_BAD_GATEWAY)

        data = chapa_resp.json() if chapa_resp.headers.get("Content-Type", "").startswith("application/json") else {"status": "failed"}
        chapa_status = data.get("status")

        if chapa_status == "success":
            payment.status = Payment.STATUS_COMPLETED
            payment.save(update_fields=["status", "updated_at"])
            # Send confirmation email via Celery if available
            if send_payment_confirmation_email:
                try:
                    send_payment_confirmation_email.delay(
                        to_email=payment.booking.guest.email,
                        booking_id=payment.booking_id,
                        amount=str(payment.amount),
                        tx_ref=payment.tx_ref,
                    )
                except Exception:
                    # Gracefully ignore email errors
                    pass
        else:
            payment.status = Payment.STATUS_FAILED
            payment.save(update_fields=["status", "updated_at"])

        return Response(
            {
                "status": "success" if chapa_status == "success" else "failed",
                "payment_status": payment.status,
                "data": data.get("data"),
            },
            status=drf_status.HTTP_200_OK if chapa_status == "success" else drf_status.HTTP_400_BAD_REQUEST,
        )

@method_decorator(csrf_exempt, name="dispatch")
class ChapaWebhookView(APIView):
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_summary="Chapa Webhook",
        operation_description="Webhook endpoint to receive Chapa payment status updates and update local Payment immediately.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "tx_ref": openapi.Schema(type=openapi.TYPE_STRING, description="Transaction reference"),
                "status": openapi.Schema(type=openapi.TYPE_STRING, description="Payment status from Chapa (success/failed)"),
                "amount": openapi.Schema(type=openapi.TYPE_STRING),
                "currency": openapi.Schema(type=openapi.TYPE_STRING),
                "signature": openapi.Schema(type=openapi.TYPE_STRING, description="Optional signature for verification"),
                "data": openapi.Schema(type=openapi.TYPE_OBJECT),
            },
        ),
        responses={
            200: openapi.Response(description="Webhook processed"),
            400: openapi.Response(description="Invalid payload"),
            404: openapi.Response(description="Payment not found"),
        },
        tags=["Payments"],
    )
    def post(self, request):
        tx_ref = request.data.get("tx_ref")
        status_value = request.data.get("status")
        if not tx_ref:
            return Response({"detail": "tx_ref is required"}, status=drf_status.HTTP_400_BAD_REQUEST)

        try:
            payment = Payment.objects.get(tx_ref=tx_ref)
        except Payment.DoesNotExist:
            return Response({"detail": "Payment not found"}, status=drf_status.HTTP_404_NOT_FOUND)

        # If webhook indicates success, mark completed; else failed.
        if str(status_value).lower() == "success":
            payment.status = Payment.STATUS_COMPLETED
        else:
            payment.status = Payment.STATUS_FAILED
        payment.save(update_fields=["status", "updated_at"])

        # Optionally send confirmation email
        if payment.status == Payment.STATUS_COMPLETED and send_payment_confirmation_email:
            try:
                send_payment_confirmation_email.delay(
                    to_email=payment.booking.guest.email,
                    booking_id=payment.booking_id,
                    amount=str(payment.amount),
                    tx_ref=payment.tx_ref,
                )
            except Exception:
                pass

        return Response({"status": "ok", "payment_status": payment.status})

class PaymentCallbackView(TemplateView):
    template_name = "listings/callback.html"
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_summary="Payment Callback Page",
        operation_description="User-facing callback page. Verifies payment using tx_ref and renders a confirmation message.",
        manual_parameters=[
            openapi.Parameter(
                name="tx_ref",
                in_=openapi.IN_QUERY,
                required=True,
                type=openapi.TYPE_STRING,
                description="Transaction reference",
            )
        ],
        tags=["Payments"],
    )
    def get(self, request, *args, **kwargs):
        tx_ref = request.GET.get("tx_ref")
        context = {"tx_ref": tx_ref, "status": "unknown", "message": ""}
        if not tx_ref:
            context["status"] = "error"
            context["message"] = "Missing tx_ref"
            return render(request, self.template_name, context)

        try:
            payment = Payment.objects.get(tx_ref=tx_ref)
        except Payment.DoesNotExist:
            context["status"] = "error"
            context["message"] = "Payment not found"
            return render(request, self.template_name, context)

        headers = {
            "Authorization": f"Bearer {getattr(settings, 'CHAPA_SECRET_KEY', '')}",
            "Content-Type": "application/json",
        }
        if not headers["Authorization"].strip():
            context["status"] = "error"
            context["message"] = "Payment verification unavailable (missing CHAPA_SECRET_KEY)"
            return render(request, self.template_name, context)

        verify_url = f"https://api.chapa.co/v1/transaction/verify/{tx_ref}"
        try:
            chapa_resp = requests.get(verify_url, headers=headers, timeout=20)
            data = chapa_resp.json() if chapa_resp.headers.get("Content-Type", "").startswith("application/json") else {"status": "failed"}
        except requests.RequestException:
            data = {"status": "failed"}

        if data.get("status") == "success":
            payment.status = Payment.STATUS_COMPLETED
            context["status"] = "success"
            context["message"] = "Payment completed successfully."
            # send email if available
            if send_payment_confirmation_email:
                try:
                    send_payment_confirmation_email.delay(
                        to_email=payment.booking.guest.email,
                        booking_id=payment.booking_id,
                        amount=str(payment.amount),
                        tx_ref=payment.tx_ref,
                    )
                except Exception:
                    pass
        else:
            payment.status = Payment.STATUS_FAILED
            context["status"] = "failed"
            context["message"] = data.get("message", "Payment verification failed.")

        payment.save(update_fields=["status", "updated_at"])
        context["booking"] = payment.booking
        context["amount"] = payment.amount
        context["currency"] = payment.currency
        return render(request, self.template_name, context)
