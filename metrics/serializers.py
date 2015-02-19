from .models import *
from django.http import Http404
from rest_framework import serializers
from bets.serializers import BetShortSerializer


class WidgetSerializer(serializers.ModelSerializer):
    bets = BetShortSerializer(many=True, read_only=True, source='get_random_bets')
    next_bets = BetShortSerializer(many=True, read_only=True, source='get_random_next_bets')
    bg_pic = serializers.Field(source='get_bg_pic_url')
    header_pic = serializers.Field(source='get_header_pic_url')
    footer_pic = serializers.Field(source='get_footer_pic_url')
    
    class Meta:
        model = Widget
        fields = ('name', 'bets', 'next_bets', 'bg_pic', 'header_pic', 'header_link', 'footer_pic', 'footer_link', 'twitter_share_text',)
