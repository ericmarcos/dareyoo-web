from django.db import IntegrityError, transaction
from django.db.models import Q
from rest_framework import viewsets, permissions, renderers, status, mixins, generics
from rest_framework.decorators import link, action
from rest_framework.response import Response
#from haystack.query import SearchQuerySet
from users.models import DareyooUserException
from users.views import DareyooUserViewSet
from users.serializers import *
from .models import *
from .serializers import BetSerializer, BidSerializer, PaginatedBetSerializer
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow the author to edit the bet.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        return request.method in permissions.SAFE_METHODS or obj.author == request.user


class IsAuthenticatedOrIsGlobal(permissions.BasePermission):

    def has_permission(self, request, view):
        return request.user.is_authenticated() or request.QUERY_PARAMS.get('global')


class CanArbitrate(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        #Introducing circular dependency with gamification module
        return request.user.points.level() >= settings.REFEREE_MIN_LEVEL


class BetViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """
    API endpoint that allows bets to be viewed or created, not modified or destroyed.
    """
    model = Bet
    serializer_class = BetSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly)
    lookup_field = 'slug'

    def get_queryset(self):
        if self.request.user.is_authenticated():
            user = self.request.user
            return Bet.objects.filter(Q(public=True) | Q(author=user) | Q(recipients=user)).distinct()
        else:
            return Bet.objects.filter(public=True)
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.DATA, files=request.FILES)
        if serializer.is_valid():
            try:
                self.pre_save(serializer.object)
                self.object = serializer.save(force_insert=True)
                self.post_save(self.object, created=True)
                invites = request.DATA.get('invites')
                self.object.invite(invites)
                headers = self.get_success_headers(serializer.data)
                return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
            except (BetException, DareyooUserException) as e:
                return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def pre_save(self, obj):
        """Force author to the current user on save"""
        obj.set_author(self.request.user)
        return super(BetViewSet, self).pre_save(obj)

    @action(permission_classes=[permissions.IsAuthenticated], methods=['GET', 'POST'], renderer_classes=[renderers.JSONRenderer, renderers.BrowsableAPIRenderer])
    def bids(self, request, *args, **kwargs):
        bet = self.get_object()
        user = self.request.user
        if request.method == 'GET':
            bids = bet.bids.all()
            serializer = BidSerializer(bids, many=True, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        elif request.method == 'POST':
            serializer = BidSerializer(data=request.DATA, files=request.FILES, context={'request': request})
            if serializer.is_valid():
                bid = serializer.object
                try:
                    auto_participate = request.QUERY_PARAMS.get('auto_participate', False)
                    bet.add_bid(bid, user, auto_participate)
                    return Response(serializer.data, status=status.HTTP_201_CREATED)
                except (BetException, DareyooUserException) as e:
                    return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({'detail': "Data not valid"}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'detail': "Method not allowed"}, status=status.HTTP_400_BAD_REQUEST)

    @action(permission_classes=[permissions.IsAuthenticated], renderer_classes=[renderers.JSONRenderer, renderers.BrowsableAPIRenderer])
    def accept_bet(self, request, *args, **kwargs):
        bet = self.get_object()
        user = self.request.user
        try:
            bet.accept_bet(user)
            bet.save()
            serializer = BetSerializer(bet, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except (BetException, DareyooUserException) as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['DELETE', 'POST'], renderer_classes=[renderers.JSONRenderer, renderers.BrowsableAPIRenderer])
    def accept_bid(self, request, *args, **kwargs):
        bet = self.get_object()
        user = self.request.user
        bid_id = request.DATA.get('bid_id', None)
        try:
            bet.accept_bid(bid_id)
            bet.save()
            serializer = BetSerializer(bet, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except (BetException, DareyooUserException) as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(renderer_classes=[renderers.JSONRenderer, renderers.BrowsableAPIRenderer])
    def remove_bid(self, request, *args, **kwargs):
        bet = self.get_object()
        user = self.request.user
        bid_id = request.DATA.get('bid_id', None)
        try:
            bet.remove_bid(bid_id)
            bet.save()
            serializer = BetSerializer(bet, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except (BetException, DareyooUserException) as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(renderer_classes=[renderers.JSONRenderer, renderers.BrowsableAPIRenderer])
    def resolve(self, request, *args, **kwargs):
        bet = self.get_object()
        user = self.request.user
        try:
            claim = int(request.DATA.get('claim'))
        except:
            claim = request.DATA.get('claim')
        claim_lottery_winner = request.DATA.get('claim_lottery_winner', None)
        claim_message = request.DATA.get('claim_message', "")
        try:
            bet.resolve(claim=claim, claim_lottery_winner=claim_lottery_winner, claim_message=claim_message)
            bet.complaining()
            bet.save()
            serializer = BetSerializer(bet, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except (BetException, DareyooUserException) as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(permission_classes=[permissions.IsAuthenticated, CanArbitrate], renderer_classes=[renderers.JSONRenderer, renderers.BrowsableAPIRenderer])
    def arbitrate(self, request, *args, **kwargs):
        bet = self.get_object()
        user = self.request.user
        try:
            referee_claim = int(request.DATA.get('claim'))
        except:
            referee_claim = request.DATA.get('claim')
        referee_lottery_winner = request.DATA.get('claim_lottery_winner', None)
        referee_message = request.DATA.get('claim_message', "")
        try:
            bet.arbitrate(user, claim=referee_claim, claim_lottery_winner=referee_lottery_winner, claim_message=referee_message)
            bet.closed_conflict()
            bet.save()
            serializer = BetSerializer(bet, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except (BetException, DareyooUserException) as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class BidViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """
    API endpoint that allows bids to be viewed or created, not modified or destroyed.
    """
    model = Bid
    serializer_class = BidSerializer
    user_short_serializer_class = DareyooUserShortSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly)

    def get_queryset(self):
        if self.request.user.is_authenticated():
            user = self.request.user
            return Bid.objects.filter(Q(bet__public=True) | Q(author=user) | Q(bet__author=user) | Q(bet__recipients=user)).distinct()
        else:
            return Bid.objects.filter(bet__public=True)

    @link(renderer_classes=[renderers.JSONRenderer, renderers.BrowsableAPIRenderer])
    def participants(self, request, *args, **kwargs):
        bid = self.get_object()
        serializer_class = self.user_short_serializer_class
        serializer = serializer_class(bid.participants.all(), many=True, context={'request': request})
        return Response(serializer.data)

    @action(permission_classes=[permissions.IsAuthenticated], renderer_classes=[renderers.JSONRenderer, renderers.BrowsableAPIRenderer])
    def add_participant(self, request, *args, **kwargs):
        bid = self.get_object()
        user = self.request.user
        try:
            bid.add_participant(user)
            serializer = BidSerializer(bid, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except (BetException, DareyooUserException) as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(permission_classes=[permissions.IsAuthenticated], renderer_classes=[renderers.JSONRenderer, renderers.BrowsableAPIRenderer])
    def complain(self, request, *args, **kwargs):
        bid = self.get_object()
        user = self.request.user
        try:
            claim = int(request.DATA.get('claim'))
        except:
            claim = request.DATA.get('claim')
        claim_message = request.DATA.get('claim_message', "")
        try:
            if claim == bid.bet.claim and not bid.bet.is_lottery():
                bid.bet.closed_ok()
            else:
                bid.complain(user, claim=claim, claim_message=claim_message)
                bid.save()
                bid.bet.arbitrating()
            serializer = BidSerializer(bid, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except (BetException, DareyooUserException) as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class SearchBetsList(generics.ListAPIView):
    model = Bet
    serializer_class = BetSerializer

    def get_queryset(self):
        user = self.request.user
        query = self.request.QUERY_PARAMS.get('q')
        order = self.request.QUERY_PARAMS.get('order', '-created_at')

        sqs = Bet.objects.all()
        sqs = sqs.bidding()
        if user.is_authenticated():
            sqs = sqs.involved(user) | sqs.public()
        else:
            sqs = sqs.public()
        if query:
            sqs = sqs.search(query)
        sqs = sqs.order_by(order)
        return sqs.distinct()


class TimelineList(generics.ListAPIView):
    model = Bet
    serializer_class = BetSerializer
    permission_classes = (IsAuthenticatedOrIsGlobal,)

    def get_queryset(self):
        user = self.request.user
        bet_state = self.request.QUERY_PARAMS.get('state', 'bidding')
        bet_type = self.request.QUERY_PARAMS.get('type', None)
        all_bets = self.request.QUERY_PARAMS.get('global', None)
        order = self.request.QUERY_PARAMS.get('order', '-created_at')
        qs = Bet.objects.all()
        if all_bets:
            #Global timeline: all public bets plus private bets where user is involved
            if self.request.user.is_authenticated():
                qs = qs.involved(user) | qs.public()
            else:
                qs = qs.public()
        else:
            #User timeline
            qs = qs.involved(user) | qs.following(user)
        if bet_state:
            qs = qs.state(bet_state)
        if bet_type:
            qs = qs.type(bet_type)
        if not order in ('-created_at', 'complained_at', 'bidding_deadline'):
            order = '-created_at'
        return qs.distinct().order_by(order)


class OpenBetsList(generics.ListAPIView):
    model = Bet
    serializer_class = BetSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        qs = Bet.objects.open(self.request.user)
        return qs.order_by('-created_at').distinct()


class DareyooUserBetViewSet(DareyooUserViewSet):
    bets_serializer_class = PaginatedBetSerializer

    @link(renderer_classes=[renderers.JSONRenderer, renderers.BrowsableAPIRenderer])
    def bets(self, request, *args, **kwargs):
        user = self.get_object()
        all_bets = request.QUERY_PARAMS.get('all', False)
        bet_state = request.QUERY_PARAMS.get('state', None)
        bet_type = request.QUERY_PARAMS.get('type', None)
        page = request.QUERY_PARAMS.get('page')

        qs = Bet.objects.all().created_by(user)

        if bet_state:
            qs = qs.state(bet_state)
        elif not all_bets:
            qs = qs.open()
        if bet_type:
            qs = qs.type(bet_type)
        if not request.user.is_authenticated():
            qs = qs.public()
        elif user != request.user:
            qs = qs.public() | qs.sent_to(request.user)

        paginator = Paginator(qs.order_by('-created_at').distinct(), 10)

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
        serializer = PaginatedBetSerializer(bets, context=serializer_context)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @link(renderer_classes=[renderers.JSONRenderer, renderers.BrowsableAPIRenderer])
    def open_bets(self, request, *args, **kwargs):
        user = self.get_object()
        bet_state = request.QUERY_PARAMS.get('state', None)
        bet_type = request.QUERY_PARAMS.get('type', None)

        qs = Bet.objects.open(user)
        if bet_state:
            qs = qs.state(bet_state)
        if bet_type:
            qs = qs.type(bet_type)
        if not request.user.is_authenticated():
            qs = qs.public()
        elif user != request.user:
            qs = qs.public() | qs.sent_to(request.user)

        qs = qs.distinct().order_by('-created_at')

        serializer = self.bets_serializer_class(qs, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    #@link(renderer_classes=[renderers.JSONRenderer, renderers.BrowsableAPIRenderer])
    #def n_bets(self, request, *args, **kwargs):
    #    user = self.get_object()
    #    all_bets = request.QUERY_PARAMS.get('all', False)
    #    bet_state = request.QUERY_PARAMS.get('state', None)
    #    bet_type = request.QUERY_PARAMS.get('type', None)
    #    
    #    qs = Bet.objects.all().creted_by(user)
    #    if bet_state:
    #        qs = qs.state(bet_state)
    #    elif not all_bets:
    #        qs = qs.open()
    #    if bet_type:
    #        qs = qs.type(bet_type)
    #
    #    return Response({'count': qs.count()}, status=status.HTTP_200_OK)
