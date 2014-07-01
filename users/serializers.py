from .models import DareyooUser
from rest_framework import serializers
from rest_framework.reverse import reverse


class DareyooUserFullSerializer(serializers.HyperlinkedModelSerializer):
    following = serializers.Field(source='n_following')
    followers = serializers.Field(source='n_followers')
    im_following = serializers.SerializerMethodField('get_im_following')
    following_me = serializers.SerializerMethodField('get_following_me')
    pic = serializers.Field(source='get_profile_pic_url')
    upload_pic_url = serializers.HyperlinkedIdentityField(view_name='dareyoouser-pic-upload')
    followers_url = serializers.HyperlinkedIdentityField(view_name='dareyoouser-followers')
    following_url = serializers.HyperlinkedIdentityField(view_name='dareyoouser-following')
    follow_url = serializers.HyperlinkedIdentityField(view_name='dareyoouser-follow')
    unfollow_url = serializers.HyperlinkedIdentityField(view_name='dareyoouser-unfollow')

    class Meta:
        model = DareyooUser
        fields = ('url', 'id', 'email', 'username', 'description', 'pic', 'upload_pic_url',
             'following', 'followers','coins_available', 'coins_locked', 'followers_url',
             'following_url', 'follow_url', 'unfollow_url', 'im_following', 'following_me',
             'email_notifications')
        read_only_fields = ('coins_available', 'coins_locked',)

    def get_im_following(self, obj):
        user = self.context['request'].user
        if user.is_authenticated() and user != obj:
            return user.is_following(obj.id)
        return False

    def get_following_me(self, obj):
        user = self.context['request'].user
        if user.is_authenticated() and user != obj:
            return obj.is_following(user.id)
        return False

    def to_native(self, obj):
        req = self.context.get('request')
        authenticated = req.user.is_authenticated()
        if self.context['request'].user != obj:
            self.fields.pop('email', None)
            self.fields.pop('coins_available', None)
            self.fields.pop('coins_locked', None)
            self.fields.pop('upload_pic', None)
            self.fields.pop('email_notifications', None)
        elif authenticated: # me!
            self.fields.pop('im_following', None)
            self.fields.pop('following_me', None)
            self.fields.pop('follow', None)
            self.fields.pop('unfollow', None)
        if not authenticated:
            self.fields.pop('im_following', None)
            self.fields.pop('following_me', None)
            self.fields.pop('follow', None)
            self.fields.pop('unfollow', None)
            self.fields.pop('email_notifications', None)
        return super(DareyooUserFullSerializer, self).to_native(obj)


class DareyooUserShortSerializer(serializers.HyperlinkedModelSerializer):
    pic = serializers.Field(source='get_profile_pic_url')
    im_following = serializers.SerializerMethodField('get_im_following')
    following_me = serializers.SerializerMethodField('get_following_me')

    def get_im_following(self, obj):
        user = self.context['request'].user
        if user.is_authenticated() and user != obj:
            return user.is_following(obj.id)
        return False

    def get_following_me(self, obj):
        user = self.context['request'].user
        if user.is_authenticated() and user != obj:
            return obj.is_following(user.id)
        return False
        
    class Meta:
        model = DareyooUser
        fields = ('id', 'url', 'username', 'pic', 'im_following', 'following_me')
