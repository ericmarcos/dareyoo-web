from django.db import IntegrityError, transaction
from django.db.models import Q
from rest_framework import viewsets, permissions, renderers, status, mixins, generics
from rest_framework.decorators import link, action
from rest_framework.response import Response
from .models import *
from .serializers import NotificationSerializer


class IsRecipient(permissions.BasePermission):
    """
    Custom permission to only allow the recipient to read the notification.
    """

    def has_object_permission(self, request, view, obj):
        return obj.recipient == request.user


class IsRecipientReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow the recipient to read the notification.
    """

    def has_object_permission(self, request, view, obj):
        return request.method in permissions.SAFE_METHODS and obj.recipient == request.user


class NotificationViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """
    API endpoint that allows notifications to be viewed.
    """
    model = Notification
    serializer_class = NotificationSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, IsRecipientReadOnly)

    def get_queryset(self):
        if self.request.user.is_authenticated():
            user = self.request.user
            return Notification.objects.filter(Q(is_new=True) | Q(readed=False), recipient=user).order_by('date')
        else:
            return []

    @action(permission_classes=[permissions.IsAuthenticated, IsRecipient], renderer_classes=[renderers.JSONRenderer, renderers.BrowsableAPIRenderer])
    def mark_as_viewed(self, request, *args, **kwargs):
        notification = self.get_object()
        try:
            notification.is_new = False
            notification.save()
            serializer = NotificationSerializer(notification, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(permission_classes=[permissions.IsAuthenticated, IsRecipient], renderer_classes=[renderers.JSONRenderer, renderers.BrowsableAPIRenderer])
    def mark_as_readed(self, request, *args, **kwargs):
        notification = self.get_object()
        try:
            notification.readed = True
            notification.save()
            serializer = NotificationSerializer(notification, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
