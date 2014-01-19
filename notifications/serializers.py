from .models import *
from django.http import Http404
from rest_framework import serializers, exceptions, status
from users.serializers import DareyooUserShortSerializer


class NotificationSerializer(serializers.HyperlinkedModelSerializer):
    recipient = DareyooUserShortSerializer(read_only=True)
    #type = serializers.Field(source='get_type_name')

    class Meta:
        model = Notification