from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('video_stream', views.video_stream, name='video_stream'),
    path('visio', views.visio, name="visio"),
    #path('<str:room_name>/', views.room, name='room'),
    path('visio_conference', views.visio_menu, name='visio_menu'),
    path('visio_conference/<str:room_uuid>', views.visio_room, name="visio_room"),
]
