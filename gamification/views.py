from rest_framework import generics, views, response, status, renderers, mixins
from rest_framework.decorators import link
from rest_framework.response import Response
from bets.views import *
from .serializers import *
from .models import *


class DareyooUserBetPointsViewSet(DareyooUserBetViewSet):
    serializer_class = DareyooUserPointsFullSerializer
    short_serializer_class = DareyooUserPointsShortSerializer
    bets_serializer_class = BetPointsSerializer

    @link(renderer_classes=[renderers.JSONRenderer, renderers.BrowsableAPIRenderer])
    def tournaments(self, request, *args, **kwargs):
        user = self.get_object()
        qs = Tournament.objects.all().is_participant(user)

        serializer = TournamentSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class BetPointsViewSet(BetViewSet):
    serializer_class = BetPointsSerializer


class WeekRankingList(views.APIView):
    queryset = UserPoints.objects.all()

    def get(self, request, format=None):
        tag = request.QUERY_PARAMS.get('tag')
        ranking = UserPoints.objects.week_ranking(tag=tag)
        serializer = RankingSerializer(ranking, context={'request': request}, many=True)
        return response.Response(serializer.data, status=status.HTTP_200_OK)


class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow the author to edit the tournament.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        return request.method in permissions.SAFE_METHODS or obj.author == request.user


class TournamentViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """
    API endpoint that allows bets to be viewed or created, not modified or destroyed.
    """
    model = Tournament
    serializer_class = TournamentSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly)

    @action(renderer_classes=[renderers.JSONRenderer, renderers.BrowsableAPIRenderer])
    def pic_upload(self, request, *args, **kwargs):
        tournament = self.get_object()
        ext = "jpg" if request.FILES['tournament_pic'].content_type == 'image/jpeg' else 'png'
        request.FILES['profile_pic'].name = '{0}_tournament.{1}'.format(tournament.id, ext)
        tournament.pic = request.FILES['tournament_pic']
        tournament.save()
        return Response({'status': 'Profile pic uploaded successfully.', 'url': tournament.pic._get_url()})


class TimelinePointsList(TimelineList):
    serializer_class = BetPointsSerializer
