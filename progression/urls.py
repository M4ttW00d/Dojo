from django.urls import path
from . import views

urlpatterns = [
    path('', views.ProgressionSettingsView.as_view(), name='progression_settings'),
    path('stages/add/', views.AddStageView.as_view(), name='progression_stage_add'),
    path('stages/<int:pk>/delete/', views.DeleteStageView.as_view(), name='progression_stage_delete'),
    path('stages/<int:pk>/move/', views.MoveStageView.as_view(), name='progression_stage_move'),
]
