import os
import random

import rest_framework.decorators as rdec
from django.conf import settings
from django.db import models, transaction
from django.db.models import Case, CharField, Count, Exists, OuterRef, Value, When
from django.http import FileResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.generics import (
    CreateAPIView,
    ListAPIView,
    ListCreateAPIView,
    RetrieveUpdateAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken

from .models import *
from .serializers import *


class RegistrationView(APIView):
    authentication_classes = []

    def post(self, request: Request):
        if request.user and request.user.is_authenticated:
            return Response(
                {"message": "Can't register while been authorized"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = UserRegistrationSerializer(data=request.data)

        if serializer.is_valid():
            userdata = serializer.data

            try:
                User.objects.get(
                    username=User.normalize_username(username=userdata["username"])
                )

                return Response(
                    {"message": "User alreaddy exists"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            except User.DoesNotExist:
                pass

            user: User = User.objects.create_user(
                username=userdata["username"],
                password=userdata["password"],
                email=userdata["email"],
            )

            print(type(user))

            refresh = RefreshToken.for_user(user)  # Создание Refesh и Access
            refresh.payload.update(
                {
                    "user_id": user.id,
                    "username": user.username,
                }
            )

            return Response(
                {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),  # Отправка на клиент
                },
                status=status.HTTP_201_CREATED,
            )
        else:
            return Response(
                {"message": "Invalid registration data"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class LoginView(APIView):
    def post(self, request: Request):
        data = request.data
        print(data)
        email = data.get("email", None)
        password = data.get("password", None)
        if email is None or password is None:
            return Response(
                {"message": "Login/Password invalid"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(
                email=email,
            )
        except User.DoesNotExist:
            return Response(
                {"message": "Invalid Login or Password"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.check_password(password):
            return Response(
                {"message": "Invalid Login or Password"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        ser = UserSerializer(data=user)
        print(ser.is_valid())

        refresh = RefreshToken.for_user(user=user)
        refresh.payload.update({"user_id": user.id, "username": user.username})
        return Response(
            {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            },
            status=status.HTTP_200_OK,
        )


class LogoutView(APIView):
    def post(self, request: Request):
        refresh_token = request.data.get(
            "refresh_token"
        )  # С клиента нужно отправить refresh token
        if not refresh_token:
            return Response(
                {"error": "Необходим Refresh token"}, status=status.HTTP_400_BAD_REQUEST
            )
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()  # Добавить его в чёрный список
        except Exception as e:
            return Response(
                {"error": "Неверный Refresh token"}, status=status.HTTP_400_BAD_REQUEST
            )
        return Response({"success": "Выход успешен"}, status=status.HTTP_200_OK)


class UsersView(ListCreateAPIView):
    serializer_class = UserSerializer
    queryset = User.objects.all()
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    lookup_field = "username"


class UserView(RetrieveUpdateDestroyAPIView):
    serializer_class = UserSerializer
    queryset = User.objects.all()
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    lookup_field = "username"

    @staticmethod
    @api_view(["GET"])
    def get_user_posts(request: Request, **kwargs):
        username = kwargs["username"]

        queryset = Post.objects.all()

        return Response(
            PostSerializer(queryset.filter(creator__username=username), many=True).data,
            status=status.HTTP_200_OK,
        )

    @staticmethod
    @api_view(["GET"])
    @rdec.permission_classes([IsAuthenticated])
    @rdec.authentication_classes([JWTAuthentication])
    def get_current_user(request: Request):
        return Response(
            UserSerializer(request.user).data,
            status=status.HTTP_200_OK,
        )


class PostsView(ListAPIView):
    serializer_class = PostSerializer
    queryset = Post.objects.all()
    # authentication_classes = [JWTAuthentication]
    # permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = self.queryset

        return queryset.filter(is_open=True)


class CreatePostView(CreateAPIView):
    serializer_class = PostSerializer
    queryset = Post.objects.all()
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request: Request):
        data = request.data

        post = Post.objects.create(
            title=data["title"],
            description=data["description"],
            payment=data["payment"],
            is_open=True,
            creator=request.user,
        )

        post.save()

        return Response(
            self.serializer_class(post).data, status=status.HTTP_201_CREATED
        )


class PostView(RetrieveUpdateDestroyAPIView):
    serializer_class = PostSerializer
    queryset = Post.objects.all()
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    lookup_field = "id"

    def get(self, request: Request, **kwargs):
        try:
            post = self.queryset.get(id=kwargs["id"])

            return_data = PostSerializer(post).data

            print(return_data)

            return Response(return_data, status=status.HTTP_200_OK)
        except Post.DoesNotExist:
            return Response(
                {"message": "Post doesn't exists"}, status=status.HTTP_404_NOT_FOUND
            )

    @staticmethod
    @api_view(["POST"])
    @rdec.permission_classes([IsAuthenticated])
    @rdec.authentication_classes([JWTAuthentication])
    @transaction.atomic
    def close(request: Request, **kwargs):
        id = kwargs.get("id", None)
        if id is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        try:
            post = Post.objects.get(id=id)
        except Post.DoesNotExist:
            return Response(
                {"message": "Post not found"}, status=status.HTTP_404_NOT_FOUND
            )

        try:
            if not post.is_open.get(id=id):
                return Response(
                    {"message": "Post already closed"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        except Post.DoesNotExist:
            pass

        post.is_deleted = True
        post.save()

        return Response(status=status.HTTP_200_OK)

    @staticmethod
    @api_view(["POST"])
    @rdec.permission_classes([IsAuthenticated])
    @rdec.authentication_classes([JWTAuthentication])
    @transaction.atomic
    def open(request: Request, **kwargs):
        id = kwargs.get("id", None)
        if id is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        try:
            post = Post.objects.get(id=id)
        except Post.DoesNotExist:
            return Response(
                {"message": "Post not found"}, status=status.HTTP_404_NOT_FOUND
            )

        current_user: User = request.user
        try:
            if not (post.creator == current_user.id):
                return Response(
                    {"message": "you don't creator post"},
                    status=status.HTTP_404_NOT_FOUND,
                )
        except Post.DoesNotExist:
            pass

        try:
            if not post.is_open.get(id=id):
                return Response(
                    {"message": "Post already closed"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        except Post.DoesNotExist:
            pass

        post.is_deleted = True
        post.save()

        return Response(status=status.HTTP_200_OK)
