from django.urls import path
from . import views

urlpatterns = [
    path('', views.register, name='register'),
    path('login/',views.user_login, name='login'),
    path('logout/',views.user_logout, name='logout'),
    path('upload/',views.upload_medical_image,name='upload'),
    path('diagnosis/<int:diagnosis_id>/download/', views.download_diagnosis_pdf, name='download_diagnosis_pdf'),
    path('simple-history/', views.simplified_history_json, name='simple-history-json'),
]
