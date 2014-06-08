from .models import *
from django.http import Http404
from rest_framework import serializers, exceptions, status
from users.serializers import *


class BidSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.Field(source='id')
    author = DareyooUserShortSerializer(read_only=True)

    class Meta:
        model = Bid


class BetSerializer(serializers.HyperlinkedModelSerializer):
    author = DareyooUserShortSerializer(read_only=True)
    #type = serializers.Field(source='get_type_name')
    bids = BidSerializer(many=True, read_only=True)
    accepted_bid = BidSerializer(read_only=True)
    winners = DareyooUserShortSerializer(read_only=True, source="winners", many=True)

    class Meta:
        model = Bet
        fields = ('author', 'title','description','amount','referee_escrow','bet_type','bet_state','odds','created_at',
                    'id', 'bidding_deadline','event_deadline','public','recipients','claim','claim_lottery_winner','claim_message',
                    'referee','referee_claim','referee_lottery_winner','url', 'bids', 'accepted_bid', 'winners')

    def restore_object(self, attrs, instance=None):
        """
        Create or update a new snippet instance, given a dictionary
        of deserialized field values.

        Note that if we don't define this method, then deserializing
        data will simply return a dictionary of items.
        """
        if instance:
            # Not updating existing instance
            return instance

        # Create new instance
        return BetFactory.create(**attrs)


class DareyooUserBetsFullSerializer(DareyooUserFullSerializer):
    open_bets = serializers.SerializerMethodField('get_open_bets')
    created_bets = serializers.SerializerMethodField('get_created_bets')
    bets_url = serializers.HyperlinkedIdentityField(view_name='dareyoouser-bets')

    def get_open_bets(self, obj):
        return Bet.objects.open(obj).distinct().count()

    def get_created_bets(self, obj):
        return Bet.objects.all().created_by(obj).distinct().count()

    class Meta:
        model = DareyooUserFullSerializer.Meta.model
        fields = DareyooUserFullSerializer.Meta.fields + ('open_bets', 'created_bets', 'bets_url')
        read_only_fields = DareyooUserFullSerializer.Meta.read_only_fields