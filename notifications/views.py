from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Notification
from .serializers import NotificationSerializer

class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if not user or not user.is_authenticated:
            return Notification.objects.none()

        return (
            Notification.objects
            .filter(recipient=user)
            .select_related("actor", "post")
        )
    # PUT/PATCH ni cheklash uchun:
    def update(self, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def partial_update(self, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(detail=True, methods=["post"])
    def read(self, request, pk=None):

        notif = self.get_object()
        notif.is_read = True
        notif.save(update_fields=["is_read"])
        return Response({"detail": "Marked as read"}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="read-all")
    def read_all(self, request):
        qs = self.get_queryset().filter(is_read=False)
        qs.update(is_read=True)
        return Response({"detail": "All notifications marked as read"}, status=status.HTTP_200_OK)
