from django.contrib.auth import get_user_model
from rest_framework import serializers

from accounts.models import CustomUser

User = get_user_model()

class CustomUserRegisterSerializer(serializers.ModelSerializer):
    password1 = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)
    class Meta:
        model = CustomUser
        fields = ('email', 'first_name', 'last_name', 'phone_number', "password1", 'password2')

    def validate(self, attrs):
        password1 = attrs.get('password1')
        password2 = attrs.get('password2')
        if password1 != password2:
            raise serializers.ValidationError("Passwords don't match | Parollar mos emas")
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password1')
        user = User.objects.create_user(password=password, **validated_data)
        return user

class CustomUserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = (
            "id",
            "email",
            'phone_number',
            "profile_pic",
            'bio',
            "first_name",
            "last_name",
            "is_active",
            'date_joined',
        )
        read_only_fields = ["id", "date_joined", 'is_active', 'email']

class EmailVerificationSerializer(serializers.Serializer):
    """
    Email va verification kodni qabul qiladi.
    """
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

class PasswordResetConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)
    password1 = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs['password1'] != attrs['password2']:
            raise serializers.ValidationError("Parollar mos emas.")
        return attrs

class UserShortProfileSerializer(serializers.ModelSerializer):
    followers_count = serializers.IntegerField(source='followers.count', read_only=True)

    following_count = serializers.IntegerField(source='followings.count', read_only=True)
    class Meta:
        model = CustomUser
        fields = ("id","email","first_name","last_name","profile_pic", "followers_count", "following_count")
        read_only_fields = ["id", "email"]