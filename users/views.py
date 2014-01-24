from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.forms import EmailField
from django.core.exceptions import ValidationError
from rest_framework import viewsets, permissions, renderers, status, generics
from rest_framework.decorators import link, action
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


@csrf_exempt
def invite_request(request):
    email = request.POST.get('email')
    if request.is_ajax():
        if email and isEmailAddressValid(email):
            if len(DareyooUser.objects.filter(email=email)) > 0:
                return HttpResponse("This email is already registered")
            else:
                u = DareyooUser.objects.create_user(email=request.POST.get('email'))
                u.save()
                return HttpResponse("ok")
        else:
            return HttpResponse("Invalid email")
    else:
        return HttpResponse("Invalid request")

 
def isEmailAddressValid(email):
    try:
        EmailField().clean(email)
        return True
    except ValidationError:
        return False