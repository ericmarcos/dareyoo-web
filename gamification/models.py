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
        return self.between(monday, sunday)

    def month(self, prev_months=0):
        first = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        first = first + relativedelta(months=-prev_months)
        last = first + relativedelta(months=1)
        return self.between(first, last)

    def between(self, start, end):
        return self.filter(created_at__range=(start, end))


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

    def sum(self):
        return self.get_queryset().sum()

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

    #level of experience
    def level(self):
        return UserPoints.level(self.sum())

    def experience(self):
        points = self.sum()
        level = UserPoints.level(points)
        bounds = UserPoints.level_bounds(points)
        return {
            'points': points,
            'level': level,
            'prev_level': bounds[0],
            'next_level': bounds[1]
        }

    def level_bounds(self):
        return UserPoints.calculate_level_bounds(self.sum())


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

    @staticmethod
    def level(points):
        return int(math.floor((max(points, 0)/1000.)**0.625) + 1)

    @staticmethod
    def level_bounds(points):
        level = UserPoints.level(points)
        return (int(math.floor((level - 1)**1.6*1000)),
                int(math.floor(level**1.6*1000)))

    def calculatePointsFromBet(self, bid=None):
        #TODO: this code is soooo ugly...
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
    loser_factor = 0.5
    lottery_factor = 0.2

    def pointsFromAmount(self, q0, q1, p):
        '''p=0 (False) means q0 is the winner. p=1 (True) means q1 is the winner
        returns a tuple (points of the winner, points of the loser)'''
        pot = q0 + q1
        risc0 = (pot*0.5/float(q0))**0.2
        risc1 = (pot*0.5/float(q1))**0.2
        if p:
            return (math.floor(pot*risc1*self.winner_factor), math.floor(pot*risc0*self.loser_factor))
        else:
            return (math.floor(pot*risc0*self.winner_factor), math.floor(pot*risc1*self.loser_factor))

    def pointsFromAmountLottery(self, pot, ni, n, p):
        '''pot = total amount involved in the lottery
        ni = # of players involved in the current bid
        n = # of players involved in the lottery
        p = current user has won (current bid is the winner bid)'''
        risc = 1 - float(ni) / n
        if p:
            return math.floor(pot*risc*self.winner_factor*self.lottery_factor)
        else:
            return math.floor(pot*risc*self.loser_factor*self.lottery_factor)


class UserBadges(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name='badges', blank=True, null=True)
    fair_play = models.SmallIntegerField(blank=True, null=True, default=0)
    max_coins = models.SmallIntegerField(blank=True, null=True, default=0)
    week_points = models.SmallIntegerField(blank=True, null=True, default=0)
    loser = models.SmallIntegerField(blank=True, null=True, default=0)
    straight_wins = models.SmallIntegerField(blank=True, null=True, default=0)
    total_wins = models.SmallIntegerField(blank=True, null=True, default=0)

    precal_total_wins = models.IntegerField(blank=True, null=True, default=0)

    def unlock_badge(self, badge, level):
        if badge in ["fair_play","max_coins","week_points","loser","straight_wins","total_wins"]:
            prev = getattr(self, badge)
            if level != prev:
                setattr(self, badge, level)
                self.save()
                gamification.signals.badge_unlocked.send(sender=self.__class__, user=self.user, badge=badge, level=level, prev_level=prev)

    @staticmethod
    def fromBet(bet):
        for user in bet.participants():
            check_fair_play(user)
            check_max_coins(user)
            check_week_points(user)
            check_loser(user)
            check_straight_wins(user)
            if user in bet.winners():
                user.badges.precal_total_wins += 1
                user.badges.save()
            check_total_wins(user)

    fair_play_levels = [4, 9, 19, 49]
    @staticmethod
    def check_fair_play(user):
        #TODO: do it at DB level!
        last_bets = user.bets.last_finished(50)
        if len(last_bets) > 0:
            current_level = user.badges.fair_play
            straight = 0
            for bet in last_bets:
                if bet.has_conflict():
                    break
                straight += 1
            if straight == 0 and current_level != 0:
                user.badges.unlock_badge("fair_play", 0)
            else:
                next_level = sorted(fair_play_levels + [straight]).index(straight)
                if next_level > current_level:
                    user.badges.unlock_badge("fair_play", next_level)


    max_coins_levels = [499, 999, 2999, 4999]
    @staticmethod
    def check_max_coins(user):
        next_level = sorted(max_coins_levels + [user.coins_available]).index(user.coins_available)
        if next_level > user.badges.max_coins:
            user.badges.unlock_badge('max_coins', next_level)

    week_points_levels = [499, 999, 2999, 4999]
    @staticmethod
    def check_week_points(user):
        week_points = user.points.week_sum()
        next_level = sorted(week_points_levels + [week_points]).index(week_points)
        if next_level > user.badges.week_points:
            user.badges.unlock_badge('week_points', next_level)

    loser_levels = [4, 9, 14, 19]
    @staticmethod
    def check_loser(user):
        last_bets = user.bets.last_finished(20)
        if len(last_bets) > 0:
            straight = 0
            for bet in last_bets:
                if user not in (bet.losers() or []):
                    break
                straight += 1
            next_level = sorted(loser_levels + [straight]).index(straight)
            if next_level > user.badges.loser:
                user.badges.unlock_badge("loser", next_level)

    straight_wins_levels = [2, 4, 9, 24]
    @staticmethod
    def check_straight_wins(user):
        last_bets = user.bets.last_finished(25)
        if len(last_bets) > 0:
            straight = 0
            for bet in last_bets:
                if user not in (bet.winners() or []):
                    break
                straight += 1
            next_level = sorted(straight_wins_levels + [straight]).index(straight)
            if next_level > user.badges.straight_wins:
                user.badges.unlock_badge("straight_wins", next_level)

    total_wins_levels = [9, 24, 49, 99]
    @staticmethod
    def check_total_wins(user):
        total_wins = user.badges.precal_total_wins
        next_level = sorted(total_wins_levels + [total_wins]).index(total_wins)
        if next_level > user.badges.total_wins:
            user.badges.unlock_badge('total_wins', next_level)



class TournamentManager(models.Manager):
    use_for_related_fields = True
    '''
    def get_queryset(self):
        return UserPointsQuerySet(self.model, using=self._db)

    def get_clean_queryset(self):
        return UserPointsQuerySet(self.model, using=self._db)
    '''


class Tournament(models.Model):
    objects = TournamentManager()

    author = models.OneToOneField(settings.AUTH_USER_MODEL, related_name='tournaments_created', blank=True, null=True)
    public = models.BooleanField(blank=True, default=True)
    only_author = models.BooleanField(blank=True, default=True)
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, null=True, related_name='tournaments')
    tag = models.CharField(max_length=255, blank=True, null=True)
    start = models.DateTimeField(blank=True, null=True, editable=False, default=None)
    end = models.DateTimeField(blank=True, null=True, editable=False, default=None)
    #reset = models.CharField(max_length=255, blank=True, null=True)
    pic = models.ImageField(upload_to='tournaments', null=True, blank=True)
    title = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True, default="")
    bets = models.ManyToManyField(Bet, blank=True, null=True, related_name='tournaments')


import gamification.signals