from .models import DareyooUser
from rest_framework import serializers


class DareyooUserFullSerializer(serializers.HyperlinkedModelSerializer):
    n_following = serializers.Field(source='n_following')
    n_followers = serializers.Field(source='n_followers')
    pic = serializers.Field(source='get_profile_pic_url')

    class Meta:
        model = DareyooUser
        fields = ('url', 'id', 'email', 'username', 'description')
        read_only_fields = ('coins_available', 'coins_locked', 'pic', 'n_following', 'n_followers',)

class DareyooUserSerializer(serializers.HyperlinkedModelSerializer):
    n_following = serializers.Field(source='n_following')
    n_followers = serializers.Field(source='n_followers')
    pic = serializers.Field(source='get_profile_pic_url')

    class Meta:
        model = DareyooUser
        fields = ('url', 'id', 'username', 'pic', 'n_following', 'n_followers')

class DareyooUserShortSerializer(serializers.HyperlinkedModelSerializer):
    pic = serializers.Field(source='get_profile_pic_url')
    class Meta:
        model = DareyooUser
        fields = ('id', 'url', 'username', 'pic')
