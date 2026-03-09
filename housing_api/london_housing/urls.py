from django.urls import path
from . import views

urlpatterns = [
    #housing endpoint
    path('housing/', views.housing_list, name="housing_list"),

    #login endpoints
    path('register/', views.register_user, name="register"),
    path('login/', views.login_user, name="login"),
    path('logout/', views.logout_user, name="logout"),
    path('rate/', views.rate_house, name="rate_house"),
    #and also edit user account
    path('user_update/', views.user_account, name="user_account"),

    #portfolio endpoint
    path('portfolio/', views.user_portfolio, name='user_portfolio'),
    #rent and buy
    path('housing/rent/', views.house_rent, name="house_rent"),
    path('housing/buy/', views.house_buy, name="house_buy"),

    #area endpoint
    path('areas/', views.area_list, name='area_list'),
]