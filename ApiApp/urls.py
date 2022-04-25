from django.urls import path
from . import views

urlpatterns = [
    path('get_uuid', views.get_uuid, name='get_uuid'),
]
