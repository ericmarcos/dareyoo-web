from rest_framework import serializers, pagination
from users.models import DareyooUser
from users.serializers import *
from bets.serializers import *
from .models import *


class UserBadgesSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = UserBadges
        fields = ('fair_play', 'max_coins', 'week_points', 'loser', 'straight_wins', 'total_wins')


class DareyooUserPointsFullSerializer(DareyooUserBetsFullSerializer):
    experience = serializers.Field(source='points.experience')
    level = serializers.Field(source='points.level')
    fair_play = serializers.Field(source='badges.fair_play')
    badges = UserBadgesSerializer(read_only=True)
    tournaments = serializers.Field(source='tournaments.all.count')
    tournaments_url = serializers.HyperlinkedIdentityField(view_name='dareyoouser-tournaments')

    class Meta:
        model = DareyooUserBetsFullSerializer.Meta.model
        fields = DareyooUserBetsFullSerializer.Meta.fields + ('fair_play', 'experience', 'level', 'tournaments', 'tournaments_url', 'badges')
        read_only_fields = DareyooUserBetsFullSerializer.Meta.read_only_fields


class DareyooUserPointsShortSerializer(DareyooUserFullSerializer):
    level = serializers.Field(source='points.level')
    fair_play = serializers.Field(source='badges.fair_play')

    class Meta:
        model = DareyooUserShortSerializer.Meta.model
        fields = DareyooUserShortSerializer.Meta.fields + ('fair_play', 'level',)


class BidPointsSerializer(BidSerializer):
    author = DareyooUserPointsShortSerializer(read_only=True)
    claim_author = DareyooUserPointsShortSerializer(read_only=True)
    points = serializers.SerializerMethodField('get_points')

    def get_points(self, obj):
        p = obj.points.first()
        if p:
            return p.points
        return 0

    class Meta:
        model = BidSerializer.Meta.model


class BetPointsSerializer(BetSerializer):
    author = DareyooUserPointsShortSerializer(read_only=True)
    points = serializers.SerializerMethodField('get_points')
    referee_points = serializers.SerializerMethodField('get_referee_points')
    bids = BidPointsSerializer(many=True, read_only=True)
    accepted_bid = BidPointsSerializer(read_only=True)
    claim_lottery_winner = BidPointsSerializer(read_only=True)
    referee_lottery_winner = BidPointsSerializer(read_only=True)

    def get_points(self, obj):
        p = obj.points.filter(user=obj.author, bid__isnull=True)
        if len(p) > 0:
            return p[0].points
        return 0

    def get_referee_points(self, obj):
        p = obj.points.filter(user=obj.referee, bid__isnull=True)
        if len(p) > 0:
            return p[0].points
        return 0
    
    class Meta:
        model = BetSerializer.Meta.model
        fields = BetSerializer.Meta.fields + ('points', 'referee_points')


class UserField(DareyooUserPointsShortSerializer):
    def to_native(self, obj):
        user = DareyooUser.objects.get(pk=obj)
        return super(UserField, self).to_native(user)


class PaginatedBetPointsSerializer(pagination.PaginationSerializer):
    class Meta:
        object_serializer_class = BetPointsSerializer


class RankingSerializer(serializers.Serializer):
    user = UserField()
    points = serializers.FloatField(source='total_points')
    position = serializers.SerializerMethodField('get_position')

    def get_position(self, obj):
        if hasattr(obj, 'position'):
            return obj.position
        else:
            return None


class TournamentSerializer(serializers.HyperlinkedModelSerializer):
    upload_pic_url = serializers.HyperlinkedIdentityField(view_name='tournament-pic-upload')
    pic = serializers.Field(source='get_pic_url')
    author = DareyooUserPointsShortSerializer()

    class Meta:
        model = Tournament
        fields = ('url', 'id', 'author', 'public', 'tag', 'start', 'end',
             'pic', 'title', 'description', 'upload_pic_url', 'only_author')