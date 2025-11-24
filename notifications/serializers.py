from rest_framework import serializers
from .models import Notification
from accounts.serializers import UserShortProfileSerializer
from blogs.serializers import PostListSerializer  # yoki qisqa serializer

class NotificationSerializer(serializers.ModelSerializer):
    actor = UserShortProfileSerializer(read_only=True)
    post = PostListSerializer(read_only=True)

    class Meta:
        model = Notification
        fields = ["id", "actor", "post", "verb", "is_read", "created_at"]
