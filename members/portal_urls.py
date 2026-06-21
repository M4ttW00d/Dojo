from django.urls import path
from . import portal_views

urlpatterns = [
    path('', portal_views.PortalView.as_view(), name='member_portal'),
    path('pay/<int:invoice_pk>/', portal_views.CreateCheckoutView.as_view(), name='portal_checkout'),
]
