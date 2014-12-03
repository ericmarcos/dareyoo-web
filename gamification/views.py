from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
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


class PrizeViewSet(viewsets.ReadOnlyModelViewSet):
    model = Prize
    serializer_class = PrizeSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, )

    def get_queryset(self):
        return Prize.objects.all().order_by('-priority')


class TournamentViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """
    API endpoint that allows bets to be viewed or created, not modified or destroyed.
    """
    model = Tournament
    serializer_class = TournamentSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly)

    def get_queryset(self):
        if self.request.user.is_authenticated():
            user = self.request.user
            return Tournament.objects.is_allowed(user).active().distinct()
        else:
            return Tournament.objects.all().public().active().distinct()

    @action(renderer_classes=[renderers.JSONRenderer, renderers.BrowsableAPIRenderer])
    def pic_upload(self, request, *args, **kwargs):
        tournament = self.get_object()
        ext = "jpg" if request.FILES['tournament_pic'].content_type == 'image/jpeg' else 'png'
        request.FILES['profile_pic'].name = '{0}_tournament.{1}'.format(tournament.id, ext)
        tournament.pic = request.FILES['tournament_pic']
        tournament.save()
        return Response({'status': 'Profile pic uploaded successfully.', 'url': tournament.pic._get_url()})

    @link(renderer_classes=[renderers.JSONRenderer, renderers.BrowsableAPIRenderer])
    def leaderboard(self, request, *args, **kwargs):
        if kwargs.get('pk') == '0':
            ranking = UserPoints.objects.all().ranking()
        else:
            tournament = self.get_object()
            week = None
            try:
                week = int(request.QUERY_PARAMS.get('week'))
            except:
                pass
            ranking = list(tournament.leaderboard(week)[:10])
            if request.user.is_authenticated():
                my_points = tournament.points(week).sum_pos(request.user)
                class Item:
                    def __init__(self, user, points, position):
                        self.user = user
                        self.total_points = points
                        self.position = position
                if my_points and my_points[1] > 10:
                    ranking.append(Item(request.user.id, my_points[0], my_points[1]))
        serializer = RankingSerializer(ranking, context={'request': request}, many=True)
        return response.Response(serializer.data, status=status.HTTP_200_OK)

    @link(renderer_classes=[renderers.JSONRenderer, renderers.BrowsableAPIRenderer])
    def bets(self, request, *args, **kwargs):
        tournament = self.get_object()
        #http://www.django-rest-framework.org/api-guide/pagination
        qs = tournament.bets.all()
        state = request.QUERY_PARAMS.get('state')
        if state == 'closed':
            qs = qs.not_bidding()
        elif state:
            qs = qs.state(state)
        paginator = Paginator(qs.order_by('-created_at'), 10)
        page = request.QUERY_PARAMS.get('page')
        try:
            bets = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            bets = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999),
            # deliver last page of results.
            bets = paginator.page(paginator.num_pages)

        serializer_context = {'request': request}
        serializer = PaginatedBetPointsSerializer(bets, context=serializer_context)
        return response.Response(serializer.data, status=status.HTTP_200_OK)

    @link(renderer_classes=[renderers.JSONRenderer, renderers.BrowsableAPIRenderer])
    def prizes(self, request, *args, **kwargs):
        tournament = self.get_object()
        #http://www.django-rest-framework.org/api-guide/pagination
        qs = tournament.prizes.all()
        paginator = Paginator(qs.order_by('-priority'), 10)
        page = request.QUERY_PARAMS.get('page')
        try:
            prizes = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            prizes = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999),
            # deliver last page of results.
            prizes = paginator.page(paginator.num_pages)

        serializer_context = {'request': request}
        serializer = PaginatedPrizeSerializer(prizes, context=serializer_context)
        return response.Response(serializer.data, status=status.HTTP_200_OK)


class TimelinePointsList(TimelineList):
    serializer_class = BetPointsSerializer


class SearchBetsPointsList(SearchBetsList):
    model = Bet
    serializer_class = BetPointsSerializer