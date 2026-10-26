from django.urls import path
from . import views

app_name = "dashboard"

urlpatterns = [
    path('', views.view_dashboard, name="dashboard"),
    path('add_plant/', views.add_plant, name="add_plant"),
    path('plants/<int:plant_id>/diagnostic/', views.add_diagnostic, name="add_diagnostic"),
    path('plants/<int:plant_id>/history/', views.plant_history, name="plant_history"),
    path('plants/<int:plant_id>/delete/', views.delete_plant, name="delete_plant"),
]

