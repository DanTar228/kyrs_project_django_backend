"""
Module for serializes models from .models
"""

from django.contrib.auth.models import User
from rest_framework import serializers

from .models import *


class SoftDeleteModelSerializer(serializers.ModelSerializer):
    """Сериализатор для модели SoftDeleteModel"""

    class Meta:
        model = SoftDeleteModel
        fields = ("id", "deleted_at", "objects", "all_objects")


class UserRegistrationSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()
    email = serializers.CharField()


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Users"""

    class Meta:
        model = User
        fields = ("id", "username", "email", "password", "registration_day")


class GlobalAdminSerializer(serializers.ModelSerializer):
    """Сериализатор для модели GlobalAdmins"""

    user = UserSerializer()

    class Meta:
        model = GlobalAdmin
        fields = ("id", "user")


class PostSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Posts"""

    creator = UserSerializer()

    class Meta:
        model = Post
        fields = (
            "id",
            "creator",
            "title",
            "payment",
            "description",
            "creator",
            "is_open",
        )

    def get_validation_exclusions(self):
        exclusions = super().get_validation_exclusions()
        return exclusions + ["creator"]


class ResourcesDataSerializer(serializers.ModelSerializer):
    """Сериализатор для модели ResourcesData"""

    class Meta:
        model = ResourcesData
        fields = ("id", "resource_url")


class ResourcesRelationSerializer(serializers.ModelSerializer):
    """Сериализатор для модели ResourcesRelations"""

    class Meta:
        model = ResourcesRelation
        fields = ("id", "post", "resource")
