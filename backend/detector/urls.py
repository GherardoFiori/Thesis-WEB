from django.urls import path
from . import views

urlpatterns = [
    path('analyze/', views.analyze_extension, name='analyze_extension'),
]