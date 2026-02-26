from django.urls import path
from . import views

urlpatterns = [
    path('housing/', views.housing_list, name="housing_list"),
    #login endpoints
    path('register/', views.register_user, name="register"),
    path('login/', views.login_user, name="login"),
    path('logout/', views.logout_user, name="logout"),
]