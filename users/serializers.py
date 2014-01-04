from .models import DareyooUser
from rest_framework import serializers


class DareyooUserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = DareyooUser
        fields = ('url', 'username', 'first_name', 'last_name')

class DareyooUserShortSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = DareyooUser
        fields = ('url', 'username',)
