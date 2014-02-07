from rest_framework import serializers
from users.models import DareyooUser
from users.serializers import DareyooUserFullSerializer, DareyooUserShortSerializer


class DareyooUserPointsFullSerializer(DareyooUserFullSerializer):
    n_following = serializers.Field(source='n_following')
    n_followers = serializers.Field(source='n_followers')
    week_total_points = serializers.Field(source='points.week_sum')
    week_total_position = serializers.Field(source='points.week_pos')

    class Meta:
        model = DareyooUser
        fields = ('url', 'id', 'username', 'first_name', 'last_name', 'coins_available', 'coins_locked', 'week_total_points', 'week_total_position', 'n_following', 'n_followers')
        read_only_fields = ('coins_available', 'coins_locked',)


class UserField(DareyooUserShortSerializer):
    def to_native(self, obj):
        user = DareyooUser.objects.get(pk=obj)
        return super(UserField, self).to_native(user)


class RankingSerializer(serializers.Serializer):
    user = UserField()
    points = serializers.FloatField(source='total_points')