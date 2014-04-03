import math
import warnings
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from django.utils import timezone
from django.db import models
from django.db.models.query import QuerySet
from django.db.models import Sum, Q
from django.conf import settings
from bets.models import Bet
from users.models import DareyooUser


class TimeRangeQuerySet(QuerySet):
    def week(self, prev_weeks=0):
        today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        monday = today + timedelta(days=-today.weekday(), weeks=-prev_weeks)
        sunday = monday + timedelta(weeks=1) # this is actually next monday
        return self.filter(created_at__range=(monday, sunday))

    def month(self, prev_months=0):
        first = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        first = first + relativedelta(months=-prev_months)
        last = first + relativedelta(months=1)
        return self.filter(created_at__range=(first, last))


class TagQuerySet(QuerySet):
    def tag(self, tag=None):
        if tag:
            return self.filter(bet__title__icontains=tag)
        else:
            return self


class UserPointsQuerySet(TimeRangeQuerySet, TagQuerySet):
    def sum(self):
        '''This method is useful when is used from a related user
        ie: user.points.week().sum() '''
        return self.aggregate(total_points=Sum('points')).get('total_points', 0) or 0


class UserPointsManager(models.Manager):
    use_for_related_fields = True

    def get_queryset(self):
        return UserPointsQuerySet(self.model, using=self._db)

    def get_clean_queryset(self):
        return UserPointsQuerySet(self.model, using=self._db)

    def week_ranking(self, prev_weeks=0, tag=''):
        qs = self.get_clean_queryset().week(prev_weeks).tag(tag)
        qs = qs.values('user').annotate(total_points=Sum('points'))
        qs = qs.order_by('-total_points')
        return qs

    def week(self, prev_weeks=0):
        return self.get_queryset().week(prev_weeks)

    def week_sum(self, prev_weeks=0, tag=''):
        '''This method is useful when is used from a related user
        ie: user.points.week_sum() '''
        return self.week(prev_weeks).tag(tag).sum()

    def week_pos(self, points=None, prev_weeks=0, tag=''):
        '''This method is useful when is used from a related user
        ie: user.points.week_pos() '''
        if not points:
            points = self.week(prev_weeks).tag(tag).sum()
        cqs = self.get_clean_queryset().week(prev_weeks).tag(tag)
        pos = cqs.values('user').annotate(total_points=Sum('points')).filter(total_points__gt=points).count()
        return pos + 1

    def month(self, prev_months=0):
        return self.get_queryset().month(prev_months)

    def month_sum(self, prev_months=0, tag=''):
        '''This method is useful when is used from a related user
        ie: user.points.month_sum() '''
        return self.month(prev_months).tag(tag).sum()

    def month_pos(self, points=None, prev_months=0, tag=''):
        '''This method is useful when is used from a related user
        ie: user.points.month_pos() '''
        if not points:
            points = self.month(prev_months).tag(tag).sum()
        cqs = self.get_clean_queryset().month(prev_months).tag(tag)
        pos = cqs.values('user').annotate(total_points=Sum('points')).filter(total_points__gt=points).count()
        return pos + 1


class UserPointsFactory:

    @staticmethod
    def fromBet(bet):
        if bet.winners():
            if bet.is_lottery():
                for bid in bet.bids.all():
                    for p in bid.participants.all():
                        u = UserPoints()
                        u.bet = bet
                        u.user = p
                        u.calculatePointsFromBet(bid)
                        u.save()
            else:
                u = UserPoints()
                u.bet = bet
                u.user = bet.author
                u.calculatePointsFromBet()
                u.save()
                u.id = None
                u.user = bet.accepted_bid.author
                u.calculatePointsFromBet()
                u.save()
            if bet.referee:
                u.id = None
                u.user = bet.referee
                u.calculatePointsFromBet()
                u.save()


class UserPoints(models.Model):
    objects = UserPointsManager()

    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='points', blank=True, null=True)
    bet = models.ForeignKey(Bet, related_name='points', blank=True, null=True)
    points = models.FloatField(blank=True, null=True, default=0)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True, editable=False)


    def calculatePointsFromBet(self, bid=None):
        winners = self.bet.winners() if self.bet else None
        ref = self.bet.referee if self.bet else None
        if ref:
            if self.bet.is_lottery():
                if ref == self.user:
                    self.points = 10*self.bet.pot()
                elif self.user == bid.claim_author:
                    if self.bet.referee_lottery_winner == bid or (self.bet.referee_claim == Bet.CLAIM_NULL and bid.claim == Bet.CLAIM_NULL):
                        pass
                    else:
                        self.points = -10*self.bet.pot()
                elif self.user == self.bet.author:
                    if self.bet.referee_lottery_winner == self.bet.claim_lottery_winner or (self.bet.referee_claim == Bet.CLAIM_NULL and self.bet.claim == Bet.CLAIM_NULL):
                        pass
                    else:
                        self.points = -10*self.bet.pot()
                else:
                    self.points = self.pointsFromAmountLottery(self.bet.pot(), bid.participants.count(), len(self.bet.participants()), self.user in winners)
            else:
                points = self.pointsFromAmount(self.bet.amount, self.bet.accepted_bid.amount, self.bet.author == winners[0])
                if winners[0] == self.user:
                    self.points = points[0]
                elif ref == self.user:
                    self.points = 10*self.bet.pot()
                else:
                    self.points = -10*self.bet.pot()
        elif winners:
            if self.bet.is_lottery():
                self.points = self.pointsFromAmountLottery(self.bet.pot(), bid.participants.count(), len(self.bet.participants()), self.user in winners)
            else:
                points = self.pointsFromAmount(self.bet.amount, self.bet.accepted_bid.amount, self.bet.author == winners[0])
                if winners[0] == self.user:
                    self.points = points[0]
                else:
                    self.points = points[1]



    winner_factor = 4
    loser_factor = 1

    def pointsFromAmount(self, q0, q1, p):
        '''p=0 (False) means q0 is the winner. p=1 (True) means q1 is the winner'''
        pot = q0 + q1
        risc0 = (pot*0.5/q0)**0.2
        risc1 = (pot*0.5/q1)**0.2
        if p:
            return (math.floor(pot*risc1*self.winner_factor), math.floor(pot*risc0*self.loser_factor))
        else:
            return (math.floor(pot*risc0*self.winner_factor), math.floor(pot*risc1*self.loser_factor))

    def pointsFromAmountLottery(self, pot, ni, n, p):
        risc = 1 - ni / n
        if p:
            return math.floor(pot*risc*self.winner_factor)
        else:
            return math.floor(pot*risc*self.loser_factor)


import gamification.signals