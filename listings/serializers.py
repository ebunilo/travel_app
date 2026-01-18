from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Listing, Booking


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model with detailed information.
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_active', 'date_joined']
        read_only_fields = ['id', 'date_joined']


class UserCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating User objects.
    """
    password = serializers.CharField(write_only=True, min_length=8, required=False)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'password', 'is_active']
        read_only_fields = ['id']

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = User.objects.create_user(**validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class ListingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Listing
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at")

class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at")