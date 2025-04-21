from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('', views.main_page, name='main_page'),
    path('login/', views.user_login, name='login'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('user-dashboard/', views.user_dashboard, name='user_dashboard'),
    path('fraud-form/<str:policy_no>/', views.fraud_form, name='fraud_form'),
    path('predict-fraud/', views.predict_fraud, name='predict_fraud'),
    path('logout/', LogoutView.as_view(next_page='main_page'), name='logout'),
    path('document-scan/', views.document_scan, name='document_scan'),
    path('profile/', views.profile, name='profile'),


]
