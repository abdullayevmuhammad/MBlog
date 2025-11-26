from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from accounts.models import Follow
from notifications.models import Notification
from .models import Post, Comment
from .serializers import (
    PostListSerializer,
    PostDetailSerializer,
    PostCreateUpdateSerializer,
    CommentSerializer,
)

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from accounts.serializers import UserShortProfileSerializer

class IsAuthorOrAdminOrReadOnly(permissions.BasePermission):


    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        user = request.user
        if not user.is_authenticated:
            return False

        if getattr(user, 'role', None) == 'admin' or user.is_staff or user.is_superuser: 
            return True

        return obj.author_id == user.id


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.select_related("author").prefetch_related("images", "likes", "comments").filter(is_deleted=False)
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrAdminOrReadOnly]
    
    lookup_field = "slug"
    lookup_value_regex = r"[-a-zA-Z0-9_]+"

    def perform_create(self, serializer):
        author = self.request.user
        post = serializer.save(author=author)

        followers = Follow.objects.filter(following=author).select_related('follower')

        channel_layer = get_channel_layer()
        notifications = []

        for f in followers:
            if f.follower_id == author.id:
                continue

            # DB ga yozib qo'yamiz
            notif = Notification(
                recipient=f.follower,
                actor=author,
                post=post,
                verb="new_post",
            )
            notifications.append(notif)

            # WebSocket orqali real-time push
            async_to_sync(channel_layer.group_send)(
                f"user_{f.follower_id}",
                {
                    "type": "send_notification",
                    "content": {
                        "verb": "new_post",
                        "post_title": post.title,
                        "post_slug": post.slug,
                        "actor_email": author.email,
                        "actor_id": author.id,
                    },
                },
            )

        Notification.objects.bulk_create(notifications)
    def get_serializer_class(self):

        if self.action == "list":
            return PostListSerializer
        if self.action == "retrieve":
            return PostDetailSerializer
        if self.action in ["create", "update", "partial_update"]:
            return PostCreateUpdateSerializer
        return PostListSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context


    def retrieve(self, request, *args, **kwargs):
      
        instance = self.get_object()
        instance.views = (instance.views or 0) + 1
        instance.save(update_fields=["views"])

        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def like(self, request, slug=None):

        post = self.get_object()
        user = request.user

        if post.likes.filter(id=user.id).exists():
            post.likes.remove(user)
            return Response({"detail": "Unliked"}, status=status.HTTP_200_OK)
        else:
            post.likes.add(user)
            return Response({"detail": "Liked"}, status=status.HTTP_200_OK)


    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticatedOrReadOnly], url_path='likes')
    def likes(self, request, slug=None):
        post = self.get_object()
        liked_users = post.likes.all()
        serializer = UserShortProfileSerializer(liked_users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated], url_path="comment")
    def add_comment(self, request, pk=None):
        post = self.get_object()
        parent_id = request.data.get("parent_comment")
        parent_obj = None
        if parent_id is not None:
            try:
                parent_obj = Comment.objects.get(id=parent_id, post=post)
            except Comment.DoesNotExist:
                return Response({"detail": "parent_comment noto'g'ri yoki bu postga tegishli emas."}, status=status.HTTP_400_BAD_REQUEST)
        data = {
            "post": post.id,
            "content": request.data.get("content"),
            "parent_comment": parent_obj.id if parent_obj else None,
        }

        serializer = CommentSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save(author=request.user)

        return Response(serializer.data, status=status.HTTP_201_CREATED)



class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.select_related("post", "author")
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrAdminOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_queryset(self):
        qs = super().get_queryset()
        post_id = self.request.query_params.get("post")
        if post_id:
            qs = qs.filter(post_id=post_id)
        return qs