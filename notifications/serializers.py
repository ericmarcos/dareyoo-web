from .models import *
from django.http import Http404
from rest_framework import serializers, exceptions, status
from users.serializers import DareyooUserShortSerializer


class NotificationSerializer(serializers.ModelSerializer):
    recipient = DareyooUserShortSerializer(read_only=True)
    #type = serializers.Field(source='get_type_name')
    id = serializers.Field(source='id')
    bet = serializers.SerializerMethodField('get_bet_slug')
    bet_type = serializers.SerializerMethodField('get_bet_type')

    def get_bet_slug(self, obj):
        if obj.bet:
            return obj.bet.slug
        return None

    def get_bet_type(self, obj):
        if obj.bet:
            return obj.bet.bet_type
        return None

    class Meta:
        model = Notification