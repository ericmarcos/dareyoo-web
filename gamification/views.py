from rest_framework import generics, views, response, status
from bets.views import DareyooUserBetViewSet
from users.views import MeUserView
from .serializers import DareyooUserPointsFullSerializer, RankingSerializer
from .models import UserPoints

class DareyooUserBetPointsViewSet(DareyooUserBetViewSet):
    serializer_class = DareyooUserPointsFullSerializer


class MeUserPointsView(MeUserView):
    serializer_class = DareyooUserPointsFullSerializer


class WeekRankingList(views.APIView):
    queryset = UserPoints.objects.all()

    def get(self, request, format=None):
        tag = request.QUERY_PARAMS.get('tag')
        ranking = UserPoints.objects.week_ranking(tag=tag)
        serializer = RankingSerializer(ranking, context={'request': request}, many=True)
        return response.Response(serializer.data, status=status.HTTP_200_OK)