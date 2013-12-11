from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.forms import EmailField
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from rest_framework import viewsets, permissions, renderers, status
from rest_framework.decorators import link, action
from rest_framework.response import Response
from .models import DareyooUser
from .serializers import DareyooUserSerializer


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

    @action()
    def follow(self, request, *args, **kwargs):
        user = self.get_object()
        follow_user_id = request.DATA.get('user_id', None)
        if not follow_user_id:
            return Response({'error': "You must provide a valid user id"}, status=status.HTTP_400_BAD_REQUEST)
        follow_user = self.queryset.filter(pk=follow_user_id)
        if len(follow_user) == 0:
            return Response({'error': "The user %s doesn't exist" % follow_user_id}, status=status.HTTP_400_BAD_REQUEST)
        if int(follow_user_id) == user.id:
            return Response({'error': "You can't follow yourself"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            with transaction.atomic():
                user.following.add(follow_user_id)
        except IntegrityError as ie:
            return Response({'error': "User %s is already following user %s" % (user.id, follow_user_id)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_201_CREATED)

    @action()
    def unfollow(self, request, *args, **kwargs):
        user = self.get_object()
        unfollow_user_id = request.DATA.get('user_id', None)
        if not unfollow_user_id:
            return Response({'error': "You must provide a valid user id"}, status=status.HTTP_400_BAD_REQUEST)
        unfollow_user = user.following.filter(pk=unfollow_user_id)
        if len(unfollow_user) == 0:
            return Response("User %s is not following user %s" % (user.id, unfollow_user_id), status=status.HTTP_400_BAD_REQUEST)
        unfollow_user = self.queryset.filter(pk=unfollow_user_id)
        if len(unfollow_user) == 0:
            return Response("User %s doesn't exist" % unfollow_user_id, status=status.HTTP_400_BAD_REQUEST)
        user.following.remove(unfollow_user_id)
        return Response(status=status.HTTP_204_NO_CONTENT)

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