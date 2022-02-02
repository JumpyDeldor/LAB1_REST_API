from django.shortcuts import render

# Create your views here.
import datetime
import jwt
from rest_framework.exceptions import AuthenticationFailed, NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import User, ToDo
from .serialezers import UserSerializer, ToDoSerializer


class RegisterView(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class LoginView(APIView):
    def post(self, request):
        name = request.data['username']
        password = request.data['password']

        user = User.objects.get(username=name)

        if user is None:
            raise AuthenticationFailed('User not found')

        if not password == user.password:
            raise AuthenticationFailed('Wrong password')

        payload = {
            'id': user.id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=60),
            'iat': datetime.datetime.utcnow()
        }

        token = jwt.encode(payload, 'secret', algorithm='HS256')

        response = Response()

        response.set_cookie(key='jwt', value=token, httponly=True)
        response.data = {
            'message': 'Enter comlite',
            'token': token
        }

        return response


def auth(request):
    token = request.COOKIES.get('jwt')

    if not token:
        raise AuthenticationFailed('Ошибка авторизации')

    try:
        payload = jwt.decode(token, 'secret', algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        raise AuthenticationFailed('Ошибка авторизации')

    return payload


class ToDoShow(APIView):
    def get(self, request):
        payload = auth(request)

        user = User.objects.filter(id=payload['id']).first()
        todo_list = ToDo.objects.filter(user=user)
        serializer = ToDoSerializer(todo_list, many=True)

        return Response(serializer.data)


class AddTask(APIView):
    def get(self, request):
        payload = auth(request)

        user = User.objects.filter(id=payload['id']).first()
        todo_list = ToDo.objects.filter(user=user)
        serializer = ToDoSerializer(todo_list, many=True)

        return Response(serializer.data)

    def post(self, request):
        payload = auth(request)
        new_todo = ToDo(user=User.objects.filter(id=payload['id']).first(), title=request.data['title'])
        print(new_todo)
        new_todo.save()

        return Response("Task added")

    def put(self, request, pk):
        payload = auth(request)

        if not ToDo.objects.filter(id=pk).first():
            raise NotFound("Task not found")

        todo = ToDo(user=User.objects.filter(id=payload['id']).first(), pk=pk)
        todo.title = request.data['title']
        todo.save()

        return Response("Task updated")

    def delete(self, request, pk):
        payload = auth(request)

        if not ToDo.objects.filter(id=pk).first():
            raise NotFound("Task not found")

        del_todo = ToDo(user=User.objects.filter(id=payload['id']).first(), pk=pk)
        del_todo.delete()

        return Response("Task deleted")