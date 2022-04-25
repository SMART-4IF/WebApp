from django.shortcuts import render
from django.http.response import StreamingHttpResponse
from streamApp.camera import VideoCamera
import uuid


# Create your views here.
def index(request):
    return render(request, 'index.html')


def gen(camera):
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')


def video_stream(request):
    return StreamingHttpResponse(gen(VideoCamera()),
                                 content_type='multipart/x-mixed-replace; boundary=frame')


def visio(request):
    return render(request, 'visioconf/main.html')


def room(request, room_name):
    return render(request, 'visioconf/room.html', {
        'room_name': room_name
    })


def visio_menu(request):
    code = str(uuid.uuid4())
    return render(request, 'visioconf/menu.html', {
        'uuid': code
    })


def visio_room(request, room_uuid):
    return render(request, 'visioconf/main.html', {
        'room_uuid': room_uuid
    })
