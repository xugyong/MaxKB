from django.urls import include, path

from .web import urlpatterns

urlpatterns = [
    *urlpatterns,
    path('api/open/', include('open_api.urls')),
]
