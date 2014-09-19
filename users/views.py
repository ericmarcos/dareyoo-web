from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.http import Http404
from django.forms import EmailField
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.views.generic.base import RedirectView
from django.core.urlresolvers import reverse, NoReverseMatch
from StringIO import StringIO
from rest_framework import viewsets, permissions, renderers, status, generics
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import link, action, api_view
from rest_framework.response import Response
from rest_framework.exceptions import MethodNotAllowed
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
    serializer_class = DareyooUserFullSerializer
    short_serializer_class = DareyooUserShortSerializer
    mini_serializer_class = DareyooUserMiniSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, IsSelfOrReadOnly)

    def list(self, request):
        if request.QUERY_PARAMS.get('only_usernames'):
            queryset = DareyooUser.objects.only('username', 'profile_pic')
            serializer_class = self.mini_serializer_class
            serializer = serializer_class(queryset, many=True, context={'request': request})
            return Response(serializer.data)
        else:
            return super(DareyooUserViewSet, self).list(request)

    def update(self, request, pk=None):
        username = request.DATA.get('username')
        if request.user.username != username and DareyooUser.objects.filter(username=username).exists():
            raise MethodNotAllowed("This username already exists.")
        ret = super(DareyooUserViewSet, self).update(request, pk)
        if request.QUERY_PARAMS.get('new'):
            user = self.get_object()
            user.send_welcome_email()
        return ret

    @link(renderer_classes=[renderers.JSONRenderer, renderers.BrowsableAPIRenderer])
    def followers(self, request, *args, **kwargs):
        user = self.get_object()
        serializer_class = self.short_serializer_class
        serializer = serializer_class(user.followers.all(), many=True, context={'request': request})
        return Response(serializer.data)

    @link(renderer_classes=[renderers.JSONRenderer, renderers.BrowsableAPIRenderer])
    def following(self, request, *args, **kwargs):
        user = self.get_object()
        serializer_class = self.short_serializer_class
        serializer = serializer_class(user.following.all(), many=True, context={'request': request})
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


class MeRedirectView(RedirectView):
    permanent = False
    query_string = True
    pattern_name = 'dareyoouser-detail'

    def get_redirect_url(self, *args, **kwargs):
        if not self.request.user.is_authenticated():
            raise Http404
        kwargs.update({'pk': self.request.user.id})
        rest = kwargs.pop('rest', '')
        #https://github.com/django/django/blob/1.6.4/django/views/generic/base.py#L173
        if self.url:
            url = self.url % kwargs
        elif self.pattern_name:
            try:
                url = reverse(self.pattern_name, args=args, kwargs=kwargs)
            except NoReverseMatch:
                return None
        else:
            return None
        url += rest
        args = self.request.META.get('QUERY_STRING', '')
        if args and self.query_string:
            url = "%s?%s" % (url, args)
        if self.request.is_secure():
            url = 'https://' + url
        return url


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