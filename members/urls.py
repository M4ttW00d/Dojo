from django.urls import path
from . import views

urlpatterns = [
    path('', views.MemberListView.as_view(), name='member_list'),
    path('add/', views.MemberCreateView.as_view(), name='member_add'),
    path('<int:pk>/', views.MemberDetailView.as_view(), name='member_detail'),
    path('<int:pk>/edit/', views.MemberUpdateView.as_view(), name='member_edit'),
    path('<int:pk>/archive/', views.MemberArchiveView.as_view(), name='member_archive'),
    path('<int:pk>/send-welcome/', views.SendWelcomeEmailView.as_view(), name='member_send_welcome'),
]
