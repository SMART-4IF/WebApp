from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns
from . import views

urlpatterns = [
    path('keys', views.manage_items, name='items'),
    path('keys/<slug:key>', views.manage_item, name='single_item'),
    path('rooms/<slug:key>', views.manage_rooms, name='room'),
    path('access_check/<slug:key>', views.access_check, name='access_check'),
]

urlpatterns = format_suffix_patterns(urlpatterns)