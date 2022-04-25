import json

from django.shortcuts import render
from django.http import JsonResponse
import uuid


# Create your views here.

def get_uuid(request):
    code = str(uuid.uuid4())

    response = {
        'uuid': code
    }

    return JsonResponse(response)
