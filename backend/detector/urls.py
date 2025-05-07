from django.urls import path
from . import views
from django.views.decorators.csrf import ensure_csrf_cookie

urlpatterns = [
    path('csrf/', ensure_csrf_cookie(views.get_csrf_token), name='get-csrf'),
    path('analyze/', views.analyze_extension, name='analyze-extension'),
]