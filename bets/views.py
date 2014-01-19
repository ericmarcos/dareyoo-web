from django.db import IntegrityError, transaction
from django.db.models import Q
from rest_framework import viewsets, permissions, renderers, status, mixins, generics
from rest_framework.decorators import link, action
from rest_framework.response import Response
from haystack.query import SearchQuerySet
from .models import *
from users.models import DareyooUserException
from .serializers import BetSerializer, BidSerializer

class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow the author to edit the bet.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        return request.method in permissions.SAFE_METHODS or obj.author == request.user


class BetViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """
    API endpoint that allows bets to be viewed or created, not modified or destroyed.
    """
    model = Bet
    serializer_class = BetSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly)

    def get_queryset(self):
        if self.request.user.is_authenticated():
            user = self.request.user
            return Bet.objects.filter(Q(public=True) | Q(author=user) | Q(recipients=user))
        else:
            return Bet.objects.filter(public=True)
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.DATA, files=request.FILES)

        if serializer.is_valid():
            try:
                self.pre_save(serializer.object)
                self.object = serializer.save(force_insert=True)
                self.post_save(self.object, created=True)
                headers = self.get_success_headers(serializer.data)
                return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
            except (BetException, DareyooUserException) as e:
                return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def pre_save(self, obj):
        """Force author to the current user on save"""
        obj.set_author(self.request.user)
        return super(BetViewSet, self).pre_save(obj)

    @action(methods=['GET', 'POST'], renderer_classes=[renderers.JSONRenderer, renderers.BrowsableAPIRenderer])
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
                    bet.add_bid(bid, user)
                    return Response(serializer.data, status=status.HTTP_201_CREATED)
                except (BetException, DareyooUserException) as e:
                    return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({'detail': "Data not valid"}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'detail': "Method not allowed"}, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['DELETE', 'POST'], renderer_classes=[renderers.JSONRenderer, renderers.BrowsableAPIRenderer])
    def accept_bid(self, request, *args, **kwargs):
        bet = self.get_object()
        user = self.request.user
        bid_id = request.DATA.get('bid_id', None)
        try:
            bet.accept_bid(bid_id)
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
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except (BetException, DareyooUserException) as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(renderer_classes=[renderers.JSONRenderer, renderers.BrowsableAPIRenderer])
    def resolve(self, request, *args, **kwargs):
        bet = self.get_object()
        user = self.request.user
        claim = request.DATA.get('claim', None)
        claim_lottery_winner = request.DATA.get('claim_lottery_winner', None)
        claim_message = request.DATA.get('claim_message', "")
        try:
            bet.resolve(claim=claim, claim_lottery_winner=claim_lottery_winner, claim_message=claim_message)
            bet.complaining()
            serializer = BetSerializer(bet, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except (BetException, DareyooUserException) as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(permission_classes=[permissions.IsAuthenticated], renderer_classes=[renderers.JSONRenderer, renderers.BrowsableAPIRenderer])
    def arbitrate(self, request, *args, **kwargs):
        bet = self.get_object()
        user = self.request.user
        claim = request.DATA.get('claim', None)
        claim_lottery_winner = request.DATA.get('claim_lottery_winner', None)
        claim_message = request.DATA.get('claim_message', "")
        try:
            bet.arbitrate(user, claim=claim, claim_lottery_winner=claim_lottery_winner, claim_message=claim_message)
            bet.closed_conflict()
            serializer = BetSerializer(bet, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except (BetException, DareyooUserException) as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class BidViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """
    API endpoint that allows bets to be viewed or created, not modified or destroyed.
    """
    model = Bid
    serializer_class = BidSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly)

    def get_queryset(self):
        if self.request.user.is_authenticated():
            user = self.request.user
            return Bid.objects.filter(Q(bet__public=True) | Q(author=user) | Q(bet__author=user) | Q(bet__recipients=user))
        else:
            return Bid.objects.filter(bet__public=True)

    @action(permission_classes=[permissions.IsAuthenticated], renderer_classes=[renderers.JSONRenderer, renderers.BrowsableAPIRenderer])
    def add_participant(self, request, *args, **kwargs):
        bid = self.get_object()
        user = self.request.user
        try:
            bid.add_participant(user, claim=claim, claim_message=claim_message)
            serializer = BidSerializer(bid, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except (BetException, DareyooUserException) as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(permission_classes=[permissions.IsAuthenticated], renderer_classes=[renderers.JSONRenderer, renderers.BrowsableAPIRenderer])
    def complain(self, request, *args, **kwargs):
        bid = self.get_object()
        user = self.request.user
        claim = request.DATA.get('claim', None)
        claim_message = request.DATA.get('claim_message', "")
        try:
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
        sqs = SearchQuerySet().models(Bet).load_all()
        sqs = sqs.filter(bet_state='bidding')
        if self.request.user.is_authenticated():
            user = self.request.user
            sqs = sqs.filter(Q(public=True) | Q(author=user) | Q(recipients=user))
        else:
            sqs = sqs.filter(public=True)
        sqs = sqs.auto_query(self.request.DATA.get('q', ''))
        sqs = sqs.order_by('bidding_deadline')
        return sqs


class TimelineList(generics.ListAPIView):
    model = Bet
    serializer_class = BetSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        qs = Bet.objects.filter(Q(recipients=user) | Q(author__in=list(user.following.all())), bet_state='bidding')
        order = self.request.DATA.get('order', '-created_at')
        if not order in ('-created_at', '-bidding_deadline'):
            order = '-created_at'
        qs = qs.order_by(order)
        return qs
