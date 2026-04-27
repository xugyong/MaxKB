from django.urls import include, path

urlpatterns = [
    path('mini-program/api/', include('mini_program.urls')),
]
