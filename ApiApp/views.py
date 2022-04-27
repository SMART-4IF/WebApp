import json

from django.shortcuts import render
from django.http import JsonResponse
import uuid

from django.conf import settings
import redis
from rest_framework.decorators import api_view
from rest_framework import status
from rest_framework.response import Response

# Connect to our Redis instance
redis_instance = redis.StrictRedis(host=settings.REDIS_HOST,
                                   port=settings.REDIS_PORT, db=0)


# Create your views here.

def get_uuid(request):
    code = str(uuid.uuid4())

    response = {
        'uuid': code
    }

    return JsonResponse(response)


# Source : https://github.com/ro6ley/django-redis/blob/master/django_redis_demo/api/views.py
@api_view(['GET', 'POST'])
def manage_items(request, *args, **kwargs):
    if request.method == 'GET':
        items = {}
        count = 0
        for key in redis_instance.keys("*"):
            try:
                items[key.decode("utf-8")] = redis_instance.get(key)
                count += 1
            except redis.exceptions.ResponseError:
                continue
        response = {
            'count': count,
            'msg': f"Found {count} items.",
            'items': items
        }
        return Response(response, status=200)

    elif request.method == 'POST':
        item = json.loads(request.body)
        key = list(item.keys())[0]
        value = item[key]
        redis_instance.set(key, value)
        redis_instance.persist(key)
        response = {
            'msg': f"{key} successfully set to {value}"
        }
        return Response(response, 201)


# Source : https://github.com/ro6ley/django-redis/blob/master/django_redis_demo/api/views.py
@api_view(['GET', 'PUT', 'DELETE'])
def manage_item(request, *args, **kwargs):
    if request.method == 'GET':
        if kwargs['key']:
            value = redis_instance.get(kwargs['key'])
            if value:
                response = {
                    'key': kwargs['key'],
                    'value': value,
                    'msg': 'success'
                }
                return Response(response, status=200)
            else:
                response = {
                    'key': kwargs['key'],
                    'value': None,
                    'msg': 'Not found'
                }
                return Response(response, status=404)

    elif request.method == 'PUT':
        if kwargs['key']:
            request_data = json.loads(request.body)
            new_value = request_data['new_value']
            value = redis_instance.get(kwargs['key'])
            if value:
                redis_instance.set(kwargs['key'], new_value)
                redis_instance.persist(kwargs['key'])
                response = {
                    'key': kwargs['key'],
                    'value': value,
                    'msg': f"Successfully updated {kwargs['key']}"
                }
                return Response(response, status=200)
            else:
                response = {
                    'key': kwargs['key'],
                    'value': None,
                    'msg': 'Not found'
                }
                return Response(response, status=404)

    elif request.method == 'DELETE':
        if kwargs['key']:
            result = redis_instance.delete(kwargs['key'])
            if result == 1:
                response = {
                    'msg': f"{kwargs['key']} successfully deleted"
                }
                return Response(response, status=404)
            else:
                response = {
                    'key': kwargs['key'],
                    'value': None,
                    'msg': 'Not found'
                }
                return Response(response, status=404)


@api_view(['GET', 'POST', 'DELETE'])
def manage_rooms(request, *args, **kwargs):
    if request.method == 'GET':
        if kwargs['key']:
            key = 'room_' + kwargs['key']
            value = redis_instance.get(key)
            if value is not None:
                response = {
                    'key': kwargs['key'],
                    'value': value,
                    'result': 1
                }
                return Response(response, status=200)
            else:
                response = {
                    'key': kwargs['key'],
                    'value': None,
                    'result': 0
                }
                return Response(response, status=404)

    elif request.method == 'POST':
        if kwargs['key']:
            request_data = json.loads(request.body)
            key = 'room_' + kwargs['key']
            value = request_data['value']
            redis_instance.set(key, value)
            redis_instance.persist(key)
            response = {
                'msg': f"{key} successfully set to {value}",
                'result': 1
            }
            return Response(response, status=200)

    elif request.method == 'DELETE':
        if kwargs['key']:
            key = 'room_' + kwargs['key']
            result = redis_instance.delete(key)
            if result == 1:
                response = {
                    'result': f"{kwargs['key']} successfully deleted"
                }
                return Response(response, status=404)
            else:
                response = {
                    'key': kwargs['key'],
                    'value': None,
                    'result': 'Not found'
                }
                return Response(response, status=404)


@api_view(['POST'])
def access_check(request, *args, **kwargs):
    if kwargs['key']:
        request_data = json.loads(request.body)
        key = 'room_' + kwargs['key']
        value = redis_instance.get(key)
        if value is not None:
            password = request_data['value']
            if password == value.decode("utf-8"):
                response = {
                    'key': kwargs['key'],
                    'result': 1
                }
                return Response(response, status=200)
            else:
                response = {
                    'key': kwargs['key'],
                    'result': 0
                }
                return Response(response, status=200)
        else:
            response = {
                'key': kwargs['key'],
                'value': None,
                'result': 0
            }
            return Response(response, status=404)
