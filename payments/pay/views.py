from rest_framework import viewsets
from .models import Vendor, SubscriptionPlan, Branch, Payment
from .serializers import VendorSerializer, SubscriptionPlanSerializer, BranchSerializer, PaymentSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import SubscriptionPlan, Branch, Payment
from django.shortcuts import get_object_or_404
import stripe
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import json
from django.http import JsonResponse
from django.views import View


class VendorRegistrationView(APIView):
    def post(self, request):
        serializer = VendorSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VendorListView(APIView):
    def get(self, request):
        vendors = Vendor.objects.all()
        serializer = VendorSerializer(vendors, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class SubscriptionPlanListView(APIView):
    def get(self, request):
        plans = SubscriptionPlan.objects.all()
        serializer = SubscriptionPlanSerializer(plans, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class BranchCreationView(APIView):
    def post(self, request):
        serializer = BranchSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VendorBranchListView(APIView):
        def get(self, request, vendor_id):
            branches = Branch.objects.filter(vendor__id=vendor_id)
            serializer = BranchSerializer(branches, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer


class SubscriptionValidationView(APIView):
    def post(self, request):
        vendor = request.user  # Assume vendor authentication is implemented
        plan_id = request.data.get("plan_id")
        branch_count = request.data.get("branch_count", 0)

        # Validate subscription plan
        subscription_plan = get_object_or_404(SubscriptionPlan, id=plan_id)

        # Calculate total cost
        branch_charge = 1  # Example additional cost per branch
        total_cost = subscription_plan.price + (branch_charge * branch_count)

        return Response({
            "plan": subscription_plan.name,
            "base_price": subscription_plan.price,
            "branch_count": branch_count,
            "branch_charge": branch_charge * branch_count,
            "total_cost": total_cost,
        }, status=status.HTTP_200_OK)


class StripePaymentView(APIView):
    def post(self, request):
        try:
            # Set your secret key: remember to switch to your live secret key in production!
            stripe.api_key = settings.STRIPE_API_KEY

            # Extract data from the request
            amount = request.data.get('amount')  # Amount in cents
            currency = request.data.get('currency', 'usd')  # Default to USD

            if not amount:
                return Response({"error": "Amount is required"}, status=status.HTTP_400_BAD_REQUEST)

            # Create a payment intent
            intent = stripe.PaymentIntent.create(
                amount=amount,
                currency=currency,
                payment_method_types=["card"],
            )

            return Response({
                "client_secret": intent.client_secret,
                "id": intent.id
            }, status=status.HTTP_200_OK)
        except stripe.error.StripeError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class StripeWebhookView(View):
    def post(self, request, *args, **kwargs):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')
        endpoint_secret = settings.STRIPE_WEBHOOK_SECRET  # Store the webhook secret in settings

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
        except ValueError:
            return JsonResponse({'error': 'Invalid payload'}, status=400)
        except stripe.error.SignatureVerificationError:
            return JsonResponse({'error': 'Invalid signature'}, status=400)

        # Handle the event
        if event['type'] == 'payment_intent.succeeded':
            payment_intent = event['data']['object']
            payment_id = payment_intent['metadata'].get('payment_id')
            if payment_id:
                payment = Payment.objects.get(id=payment_id)
                payment.status = 'Completed'
                payment.save()
        elif event['type'] == 'payment_intent.payment_failed':
            payment_intent = event['data']['object']
            payment_id = payment_intent['metadata'].get('payment_id')
            if payment_id:
                payment = Payment.objects.get(id=payment_id)
                payment.status = 'Failed'
                payment.save()

        return JsonResponse({'status': 'success'}, status=200)
