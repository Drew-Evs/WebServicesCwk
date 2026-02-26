from django.urls import path
from . import views

urlpatterns = [
    path('housing/', views.housing_list, name="housing_list"),
]