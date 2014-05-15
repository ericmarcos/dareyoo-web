from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.forms import EmailField
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from StringIO import StringIO
from rest_framework import viewsets, permissions, renderers, status, generics
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import link, action, api_view
from rest_framework.response import Response
from .models import *
from .serializers import *


class IsSelfOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow a user to edit itself.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        return obj == request.user


class DareyooUserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = DareyooUser.objects.all()
    serializer_class = DareyooUserSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, IsSelfOrReadOnly)

    @link(renderer_classes=[renderers.JSONRenderer, renderers.BrowsableAPIRenderer])
    def followers(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = DareyooUserSerializer(user.followers.all(), many=True)
        return Response(serializer.data)

    @link(renderer_classes=[renderers.JSONRenderer, renderers.BrowsableAPIRenderer])
    def following(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = DareyooUserSerializer(user.following.all(), many=True)
        return Response(serializer.data)

    @link(permission_classes=[permissions.IsAuthenticated], renderer_classes=[renderers.JSONRenderer, renderers.BrowsableAPIRenderer])
    def is_following(self, request, *args, **kwargs):
        user = self.get_object()
        asked_user_id = request.QUERY_PARAMS.get('user_id', None)
        try:
            following = user.is_following(asked_user_id)
            return Response({'status': following}, status=status.HTTP_201_CREATED)
        except DareyooUserException as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @link(permission_classes=[])
    def pic(self, request, *args, **kwargs):
        user = self.get_object()
        if user.profile_pic and user.profile_pic._get_url():
            return Response("", status=status.HTTP_303_SEE_OTHER, headers={'Location': user.profile_pic._get_url()})
        else:
            return Response({'detail': "No profile pic available"}, status=status.HTTP_404_NOT_FOUND)

    @action(permission_classes=[permissions.IsAuthenticated, IsSelfOrReadOnly], renderer_classes=[renderers.JSONRenderer, renderers.BrowsableAPIRenderer])
    def pic_upload(self, request, *args, **kwargs):
        user = self.get_object()
        ext = "jpg" if request.FILES['profile_pic'].content_type == 'image/jpeg' else 'png'
        request.FILES['profile_pic'].name = '{0}_social.{1}'.format(user.id, ext)
        user.profile_pic = request.FILES['profile_pic']
        user.save()
        return Response({'status': 'Profile pic uploaded successfully.', 'url': user.profile_pic._get_url()})

    @action(permission_classes=[permissions.IsAuthenticated], renderer_classes=[renderers.JSONRenderer, renderers.BrowsableAPIRenderer])
    def follow(self, request, *args, **kwargs):
        user = self.get_object()
        follower = request.user
        try:
            follower.follow(user)
            return Response({'status': 'ok'}, status=status.HTTP_201_CREATED)
        except DareyooUserException as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(permission_classes=[permissions.IsAuthenticated], renderer_classes=[renderers.JSONRenderer, renderers.BrowsableAPIRenderer])
    def unfollow(self, request, *args, **kwargs):
        user = self.get_object()
        follower = request.user
        try:
            follower.unfollow(user)
            return Response({'status': 'ok'}, status=status.HTTP_201_CREATED)
        except DareyooUserException as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class MeUserView(generics.RetrieveUpdateAPIView):
    queryset = DareyooUser.objects.all()
    serializer_class = DareyooUserFullSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user


class SearchFacebookFriendsList(generics.ListAPIView):
    model = DareyooUser
    serializer_class = DareyooUserShortSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return self.request.user.get_fb_friends()


class SearchDareyooSuggestedList(generics.ListAPIView):
    model = DareyooUser
    serializer_class = DareyooUserShortSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return DareyooUser.objects.filter(is_vip=True).order_by('?')