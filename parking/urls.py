from django.urls import path
from django.urls import re_path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('admin-stats/', views.admin_statistics_view, name='admin_statistics'),
    path('', views.home_view, name='home'),
    path('services/', views.services_view, name='services'),
    path('reviews/', views.reviews_view, name='reviews'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('faq/', views.faq_view, name='faq'),
    path('register/', views.register_view, name='register'),

    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    path('add-car/', views.add_car_view, name='add_car'),
    re_path(r'^invoice/pay/(?P<invoice_id>\d+)/$', views.pay_invoice_view, name='pay_invoice'),

    re_path(r'^delete-car/(?P<car_id>\d+)/$', views.delete_car_view, name='delete_car'),
    path('staff-panel/', views.employee_dashboard_view, name='employee_dashboard'),

    path('about/', views.about_view, name='about'),
    path('contacts/', views.contacts_view, name='contacts'),
    path('privacy-policy/', views.privacy_policy_view, name='privacy_policy'),
    path('vacancies/', views.vacancies_view, name='vacancies'),

    path('check-promocode/', views.check_promocode_view, name='check_promocode'),

    path('add-parking-spot/', views.add_parking_spot_view, name='add_parking_spot'),

    re_path(r'^edit-parking-spot-price/(?P<spot_id>\d+)/$', views.edit_parking_spot_price_view,
            name='edit_parking_spot_price'),
    re_path(r'^delete-parking-spot/(?P<spot_id>\d+)/$', views.delete_parking_spot_view, name='delete_parking_spot'),
]