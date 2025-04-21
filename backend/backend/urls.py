from django.contrib import admin
from django.urls import path, include
from detector import views
from django.views.decorators.csrf import ensure_csrf_cookie

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('detector.urls')),
    path('api/csrf/', ensure_csrf_cookie(views.get_csrf_token)), 
    path('csrf/', views.get_csrf_token, name='get-csrf'),
    path('analyze/', views.analyze_extension, name='analyze-extension'),
]