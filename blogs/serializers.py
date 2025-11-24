# blogs/serializers.py
from rest_framework import serializers
from .models import Post, PostImage, Comment


class PostImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostImage
        fields = ["id", "image"]



class PostListSerializer(serializers.ModelSerializer):
    images = PostImageSerializer(read_only=True, many=True)
    likes_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            "id",
            "title",
            "slug",
            "created_at",
            "likes_count",
            "views",
            "is_liked",
            "images",
        ]

    def get_likes_count(self, obj):
        return obj.likes.count()

    def get_is_liked(self, obj):
        request = self.context.get("request")
        if not request or request.user.is_anonymous:
            return False
        return obj.likes.filter(id=request.user.id).exists()


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.ReadOnlyField(source='author.id')

    class Meta:
        model = Comment
        fields = ["id", "post", "content", "author", "created_at", "parent_comment"]
        read_only_fields = ["id", "author", "created_at"]

class PostDetailSerializer(serializers.ModelSerializer):
    images = PostImageSerializer(read_only=True, many=True)
    likes_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    comments = CommentSerializer(read_only=True, many=True)

    class Meta:
        model = Post
        fields = [
            "id",
            "title",
            "slug",
            "content",
            "author",
            "created_at",
            "updated_at",
            "likes_count",
            "views",
            "is_liked",
            "images",
            "comments",
        ]
        read_only_fields = ["id", "slug", "author", "created_at", "updated_at", "views"]

    def get_likes_count(self, obj):
        return obj.likes.count()

    def get_is_liked(self, obj):
        request = self.context.get("request")
        if not request or request.user.is_anonymous:
            return False
        return obj.likes.filter(id=request.user.id).exists()


class PostCreateUpdateSerializer(serializers.ModelSerializer):
    images = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = Post
        fields = ["title", "content", "images"]

    def create(self, validated_data):
        images = validated_data.pop("images", [])
        post = Post.objects.create(**validated_data)
        for img in images:
            PostImage.objects.create(post=post, image=img)
        return post

    def update(self, instance, validated_data):
        images = validated_data.pop("images", None)

        instance.title = validated_data.get("title", instance.title)
        instance.content = validated_data.get("content", instance.content)
        instance.save()

        if images is not None:
            instance.images.all().delete()
            for img in images:
                PostImage.objects.create(post=instance, image=img)

        return instance


