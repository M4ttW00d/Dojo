from django.urls import include, path
from . import views

urlpatterns = [
    path('', views.DashboardView.as_view(), name='org_dashboard'),
    path('members/', include('members.urls')),
]
