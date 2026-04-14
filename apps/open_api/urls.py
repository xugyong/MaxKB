from django.urls import include, path

from . import views

app_name = 'open_api'

urlpatterns = [
    path('v1/health', views.HealthView.as_view()),
    path('v1/', include('open_api.urls_v1')),
]
