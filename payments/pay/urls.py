from rest_framework.routers import DefaultRouter
from django.urls import path, include
#from .views import  SubscriptionPlanViewSet, BranchViewSet, PaymentViewSet
from .views import *

router = DefaultRouter()
router.register(r'payments', PaymentViewSet)

urlpatterns = [
    # path('pay/', include(router.urls)),
    # path('stripe-webhook/', StripeWebhookView.as_view(), name='stripe-webhook'),
    # path('stripe-payment/', StripePaymentView.as_view(), name='stripe-payment'),
    # path('vendors/', VendorListView.as_view(), name='vendor-list'),
    # path('subscription-plans/', SubscriptionPlanListView.as_view(), name='subscription-plan-list'),
    # path('branches/', BranchCreationView.as_view(), name='branch-create'),
    path('register-vendor/', VendorRegistrationView.as_view(), name='register-vendor'),
    path('vendors/', VendorListView.as_view(), name='vendor-list'),
    path('subscription-plans/', SubscriptionPlanListView.as_view(), name='subscription-plans'),
    path('create-branch/', BranchCreationView.as_view(), name='create-branch'),
    path('vendor-branches/<int:vendor_id>/', VendorBranchListView.as_view(), name='vendor-branches'),
    path('validate-subscription/', SubscriptionValidationView.as_view(), name='validate-subscription'),
    path('stripe-payment/', StripePaymentView.as_view(), name='stripe-payment'),
    path('stripe-webhook/', StripeWebhookView.as_view(), name='stripe-webhook'),
    path('', include(router.urls)),
]
