# blogs/models.py
from django.db import models
from django.utils.text import slugify
from ckeditor.fields import RichTextField
from accounts.models import CustomUser
from django.utils import timezone

class Post(models.Model):
    title = models.CharField(max_length=100)
    content = RichTextField()
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='posts')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    likes = models.ManyToManyField(CustomUser, related_name='like_posts', blank=True)
    slug = models.SlugField(unique=True, max_length=100, blank=True)
    views = models.PositiveIntegerField(default=0)

    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def delete(self, using=None, keep_parents=False):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at'])

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1

            # Slug unique bo'lishi uchun tekshiramiz
            while Post.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = slug

        super().save(*args, **kwargs)


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments', null=True)
    content = models.TextField()
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='comments')
    created_at = models.DateTimeField(auto_now_add=True)
    parent_comment = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='replies'
    )

    def __str__(self):
        return f"{self.content[:50]} by {self.author.email}"


class PostImage(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='post_images/')
