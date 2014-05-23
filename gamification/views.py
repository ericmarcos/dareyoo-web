from rest_framework import generics, views, response, status, renderers
from rest_framework.decorators import link
from rest_framework.response import Response
from bets.views import *
from .serializers import *
from .models import UserPoints


class DareyooUserBetPointsViewSet(DareyooUserBetViewSet):
    serializer_class = DareyooUserPointsFullSerializer
    short_serializer_class = DareyooUserPointsShortSerializer


class BetPointsViewSet(BetViewSet):
    serializer_class = BetPointsSerializer


class WeekRankingList(views.APIView):
    queryset = UserPoints.objects.all()

    def get(self, request, format=None):
        tag = request.QUERY_PARAMS.get('tag')
        ranking = UserPoints.objects.week_ranking(tag=tag)
        serializer = RankingSerializer(ranking, context={'request': request}, many=True)
        return response.Response(serializer.data, status=status.HTTP_200_OK)