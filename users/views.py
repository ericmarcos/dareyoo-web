from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.http import Http404
from django.shortcuts import redirect
from django.forms import EmailField
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.core.files.base import ContentFile
from django.views.generic.base import RedirectView
from django.core.urlresolvers import reverse, NoReverseMatch
from django.contrib.auth import login
from social.apps.django_app.utils import psa
from provider import scope
from provider.oauth2.models import Client
from provider.oauth2.views import AccessTokenView
from StringIO import StringIO
from rest_framework import viewsets, permissions, renderers, status, generics
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import link, action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.exceptions import MethodNotAllowed
from .models import *
from .serializers import *
from .pipelines import *
from .signals import user_activated


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
            return Response({'status': 'ok'}, status=status.HTTP_204_NO_CONTENT)
        except DareyooUserException as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

'''
class MeRedirectView(RedirectView):
    permanent = False
    query_string = True
    pattern_name = 'dareyoouser-detail'

    def get_redirect_url(self, *args, **kwargs):
        if not self.request.user.is_authenticated():
            raise Http404
        user_activated.send(sender=self.__class__, user=self.request.user)
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
'''
class MeRedirectView(APIView):
    """
    View to list all users in the system.

    * Requires token authentication.
    * Only admin users are able to access this view.
    """
    model = DareyooUser
    def get(self, request, format=None):
        """
        Return a list of all users.
        """
        if not self.request.user.is_authenticated():
            raise Http404
        user_activated.send(sender=self.__class__, user=self.request.user)
        return redirect('dareyoouser-detail', pk=self.request.user.id)

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


@api_view(['POST',])
@permission_classes([])
def register(request, format=None):
    email = request.DATA.get('email', '')
    password = request.DATA.get('password', '')
    password2 = request.DATA.get('password2', '')
    user = DareyooUser.objects.filter(email=email)
    try:
        client = Client.objects.get(client_id=request.DATA.get('client_id'))
    except:
        return Response({'detail': 'Wrong client id'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        validate_email(email)
    except ValidationError as e:
        return Response({'detail': 'Please, introduce a valid email'}, status=status.HTTP_400_BAD_REQUEST)
    if len(user) > 0 and user[0].registered == True:
        return Response({'detail': 'This email is already registered'}, status=status.HTTP_400_BAD_REQUEST)
    elif password != password2:
        return Response({'detail': 'Wrong password'}, status=status.HTTP_400_BAD_REQUEST)
    else:
        if len(user) > 0:
            user = user[0]
        else:
            user = DareyooUser(email=email)
            user.set_password(password)
            user.save()
        #Social pipeline
    pipeline_params = {'strategy': None, 'user': user, 'response':None,
                    'details': None, 'is_new': True, 'request': request}
    save_profile_picture(**pipeline_params)
    save_username(**pipeline_params)
    save_reference_user(**pipeline_params)
    save_registered(**pipeline_params)
    save_campaign(**pipeline_params)
    #promo_code(**pipeline_params)
    access_token = AccessTokenView().get_access_token(request,
        user,
        scope.to_int('read', 'write'),
        client
    )
    return Response(
        {'access_token': access_token.token,
        'expires_in': access_token.get_expire_delta(),
        'refresh_token': access_token.refresh_token.token,
        'scope': ' '.join(scope.names(access_token.scope))},
        status=status.HTTP_200_OK
    )


#http://psa.matiasaguirre.net/docs/use_cases.html#signup-by-oauth-access-token
@api_view(['POST',])
@permission_classes([])
@psa('social:complete')
def register_by_access_token(request, backend, format=None):
    # This view expects an access_token GET parameter, if it's needed,
    # request.backend and request.strategy will be loaded with the current
    # backend and strategy.
    client_id = request.DATA.get('client_id', None)

    user = request.backend.do_auth(request.DATA.get('access_token'))
    if user:
        try:
            client = Client.objects.get(client_id=client_id)
            access_token = AccessTokenView().get_access_token(request,
                user,
                scope.to_int('read', 'write'),
                client
            )
            return Response(
                {'access_token': access_token.token,
                'expires_in': access_token.get_expire_delta(),
                'refresh_token': access_token.refresh_token.token,
                'scope': ' '.join(scope.names(access_token.scope))},
                status=status.HTTP_200_OK
            )
        except:
            return Response({'detail': "Wrong client id"}, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response({'detail': "Wrong access token"}, status=status.HTTP_400_BAD_REQUEST)
