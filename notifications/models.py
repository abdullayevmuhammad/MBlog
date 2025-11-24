from django.db import models

# Create your models here.
class Notification(models.Model):
    recipient = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, related_name='notifications')
    actor = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, related_name='notifications_from_me')
    post = models.ForeignKey('blogs.Post', on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    verb = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


    def __str__(self):
        return f"{self.recipient} <- {self.actor} : {self.verb}"