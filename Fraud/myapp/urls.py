# insurance_app/urls.py
from django.urls import path
from .import views
from . import views  # Import the views from the current directory

urlpatterns = [
    #path('', views.search_form, name='search_form'),  
    #path('fraud-form/<str:policy_no>/', views.fraud_form, name='fraud_form'),
    #path('predict-fraud/', views.predict_fraud, name='predict_fraud'),
    path('', views.admin_dashboard, name='admin_dashboard'),
    path('fraud-form/<str:policy_no>/', views.fraud_form, name='fraud_form'),
    path('predict-fraud/', views.predict_fraud, name='predict_fraud'),
]
