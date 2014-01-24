from .models import DareyooUser
from rest_framework import serializers


class DareyooUserFullSerializer(serializers.HyperlinkedModelSerializer):
    n_following = serializers.Field(source='n_following')
    n_followers = serializers.Field(source='n_followers')

    class Meta:
        model = DareyooUser
        fields = ('url', 'id', 'username', 'first_name', 'last_name', 'coins_available', 'coins_locked', 'points', 'n_following', 'n_followers')
        read_only_fields = ('coins_available', 'coins_locked', 'points',)

class DareyooUserSerializer(serializers.HyperlinkedModelSerializer):
    n_following = serializers.Field(source='n_following')
    n_followers = serializers.Field(source='n_followers')

    class Meta:
        model = DareyooUser
        fields = ('url', 'id', 'username', 'first_name', 'last_name', 'n_following', 'n_followers')

class DareyooUserShortSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = DareyooUser
        fields = ('id', 'url', 'username',)
