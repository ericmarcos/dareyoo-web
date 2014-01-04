from .models import *
from django.http import Http404
from rest_framework import serializers, exceptions, status
from users.serializers import DareyooUserShortSerializer


class BetSerializer(serializers.HyperlinkedModelSerializer):
    author = DareyooUserShortSerializer(read_only=True)
    #type = serializers.Field(source='get_type_name')

    def __init__(self, *args, **kwargs):
        super(BetSerializer, self).__init__(*args, **kwargs)

        instance = self.data.get('instance', None)
        if instance and instance(instance, Bet):
            self.exclude = []
            if instance.bet_type == Bet.TYPE_SIMPLE:
                self.exclude.append('accepted_bid')


    class Meta:
        model = Bet
        fields = ('author', 'title','description','amount','referee_escrow','bet_type','bet_state','odds','accepted_bid','created_at',
                            'bidding_deadline','event_deadline','public','recipients','claim','claim_lottery_winner','claim_message',
                            'points','referee','referee_claim','referee_lottery_winner','url')

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

class BidSerializer(serializers.HyperlinkedModelSerializer):
    author = DareyooUserShortSerializer(read_only=True)

    class Meta:
        model = Bid
