from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('api/search/', views.ai_search, name='ai_search'),
    path('search/', views.search_species, name='search_species'),
    path('history/', views.get_search_history, name='search_history'),
    path('detect/camera/', views.detect_from_camera, name='detect_camera'),
    path('detect/upload/', views.detect_from_upload, name='detect_upload'),
    path('detections/', views.get_recent_detections, name='recent_detections'),

    # ── Proxy de imágenes: el servidor busca la foto, el browser no tiene restricciones
    path('img/<str:article>/', views.proxy_image, name='proxy_image'),
]

































