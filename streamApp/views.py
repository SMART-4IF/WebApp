import uuid

from django.contrib.auth.decorators import login_required
from django.http.response import StreamingHttpResponse
from django.shortcuts import render, redirect

from streamApp.camera import VideoCamera
from SmartWeb.settings import LOGIN_URL


# Create your views here.
def index(request):
    return render(request, 'home.html')


def gen(camera):
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')


@login_required(login_url=LOGIN_URL)
def video_stream(request):
    return StreamingHttpResponse(gen(VideoCamera()),
                                 content_type='multipart/x-mixed-replace; boundary=frame')


@login_required(login_url=LOGIN_URL)
def visio(request):
    return render(request, 'visioconf/main.html')


@login_required(login_url=LOGIN_URL)
def room(request, room_name):
    return render(request, 'visioconf/room.html', {
        'room_name': room_name
    })


@login_required(login_url=LOGIN_URL)
def visio_menu(request):
    code = str(uuid.uuid4())
    return render(request, 'visioconf/menu.html', {
        'uuid': code
    })


@login_required(login_url=LOGIN_URL)
def visio_room(request, room_uuid):
    return render(request, 'visioconf/main.html', {
        'room_uuid': room_uuid
    })


