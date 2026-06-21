from django.urls import path
from . import views

urlpatterns = [
    path('members/<int:member_pk>/documents/upload/', views.DocumentUploadView.as_view(), name='document_upload'),
    path('members/<int:member_pk>/documents/<int:pk>/delete/', views.DocumentDeleteView.as_view(), name='document_delete'),
    path('members/<int:member_pk>/documents/<int:pk>/download/', views.DocumentDownloadView.as_view(), name='document_download'),
]
