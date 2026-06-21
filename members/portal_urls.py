from django.urls import path
from . import portal_views

urlpatterns = [
    path('', portal_views.PortalView.as_view(), name='member_portal'),
]
