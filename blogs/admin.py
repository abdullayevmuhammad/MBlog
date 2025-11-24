# blogs/admin.py
from django.contrib import admin
from .models import Post, PostImage, Comment


class PostImageInline(admin.TabularInline):
    model = PostImage
    extra = 1


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('content', 'id', 'author', 'post', 'created_at')
    search_fields = ('content', 'author__email', 'post__title')


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    inlines = [PostImageInline, CommentInline]
    list_display = ('id', 'title', 'author', 'created_at', 'is_deleted')
    search_fields = ('title', 'author__email')
    prepopulated_fields = {"slug": ("title",)}