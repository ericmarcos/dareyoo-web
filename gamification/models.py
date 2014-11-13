import math
import warnings
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from django.utils import timezone
from django.db import models
from django.db.models.query import QuerySet
from django.db.models import Sum, Q
from django.conf import settings
from rest_framework.exceptions import APIException
from bets.models import Bet, Bid
from users.models import DareyooUser


class GamificationException(APIException):
    status_code = 400

    @property
    def detail(self):
        return str(self)


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

    def sum_pos(self, user):
        points = self.user(user).sum()
        if points > 0:
            pos = self.values('user').annotate(total_points=Sum('points')).filter(total_points__gt=points).count()
            return (points, pos + 1)
        else:
            return None

    def user(self, user):
        return self.filter(user=user)

    def ranking(self):
        qs = self.values('user')
        qs = qs.annotate(total_points=Sum('points'))
        qs = qs.order_by('-total_points')
        return qs


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
        if bet.is_lottery():
            author_participated = False
            for bid in bet.bids.all():
                for p in bid.participants.all():
                    u = UserPoints()
                    u.bet = bet
                    u.user = p
                    u.calculatePointsFromBet(bid)
                    if p == bet.author:
                        author_participated = True
                    u.save()
            # TODO: decide what to do when creator doesnt participate
            #if not author_participated:
            #    u = UserPoints()
            #    u.bet = bet
            #    u.user = bet.author
            #    u.points = bet.pot()
            #    u.save()
        else:
            u = UserPoints()
            u.bet = bet
            u.user = bet.author
            u.calculatePointsFromBet()
            u.save()
            u.id = None
            u.user = bet.accepted_bid.author
            u.calculatePointsFromBet(bet.accepted_bid)
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
    bid = models.ForeignKey(Bid, related_name='points', blank=True, null=True)
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

    def conflictWinnerPoints(self):
        ''' Extra points for winning a conflict (even if the user loses the bet) '''
        return self.bet.pot()

    def conflictLoserPoints(self):
        return -3*self.bet.pot()

    def refereePoints(self):
        return 5*self.bet.pot()

    def lotteryCreatorPoints(self):
        return math.floor(0.5*self.bet.pot())

    def calculatePointsFromBet(self, bid=None):
        #TODO: this code is soooo ugly...
        winners = self.bet.winners() if self.bet else []
        winners = winners or []
        ref = self.bet.referee if self.bet else None
        self.bid = bid
        if ref:
            if self.bet.is_lottery():
                if ref == self.user:
                    self.points = self.refereePoints()
                elif bid and self.user == bid.claim_author:
                    if self.bet.referee_lottery_winner == bid or (self.bet.referee_claim == Bet.CLAIM_NULL and bid.claim == Bet.CLAIM_NULL):
                        self.points = self.pointsFromAmountLottery(self.bet.pot(), bid.participants.count(), len(self.bet.participants()), self.bet.referee_lottery_winner == bid)
                        self.points += self.conflictWinnerPoints()
                    else:
                        self.points = self.conflictLoserPoints()
                elif self.user == self.bet.author:
                    if self.bet.referee_lottery_winner == self.bet.claim_lottery_winner or (self.bet.referee_claim == Bet.CLAIM_NULL and self.bet.claim == Bet.CLAIM_NULL):
                        self.points = self.conflictWinnerPoints()
                        '''the author wins the conflict, but maybe he hasn't participated'''
                        if self.user in self.bet.participants():
                            self.points += self.pointsFromAmountLottery(self.bet.pot(), bid.participants.count(), len(self.bet.participants()), self.user in winners)
                    else:
                        self.points = self.conflictLoserPoints()
                else:
                    self.points = self.pointsFromAmountLottery(self.bet.pot(), bid.participants.count(), len(self.bet.participants()), self.user in winners)
            else:
                points = self.pointsFromAmount(self.bet.amount, self.bet.accepted_bid.amount, winners and self.bet.author == winners[0])
                if winners and winners[0] == self.user:
                    self.points = points[0]
                    self.points += self.conflictWinnerPoints()
                elif ref == self.user:
                    self.points = self.refereePoints()
                else:
                    self.points = self.conflictLoserPoints()
        else:
            if self.bet.is_lottery():
                self.points = self.pointsFromAmountLottery(self.bet.pot(), bid.participants.count(), len(self.bet.participants()), self.user in winners)
            else:
                points = self.pointsFromAmount(self.bet.amount, self.bet.accepted_bid.amount, winners and self.bet.author == winners[0])
                if winners and winners[0] == self.user:
                    self.points = points[0]
                else:
                    self.points = points[1]



    winner_factor = 4
    loser_factor = 0.5
    lottery_factor = 0.8

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

    @classmethod
    def fromBet(cls, bet):
        for user in bet.participants():
            UserBadges.check_fair_play(user)
            UserBadges.check_max_coins(user)
            UserBadges.check_week_points(user)
            UserBadges.check_loser(user)
            UserBadges.check_straight_wins(user)
            if user in (bet.winners() or []):
                user.badges.precal_total_wins += 1
                user.badges.save()
            UserBadges.check_total_wins(user)

    fair_play_levels = [4, 9, 19, 49]
    @classmethod
    def check_fair_play(cls, user):
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
                next_level = sorted(UserBadges.fair_play_levels + [straight]).index(straight)
                if next_level > current_level:
                    user.badges.unlock_badge("fair_play", next_level)


    max_coins_levels = [499, 999, 2999, 4999]
    @classmethod
    def check_max_coins(cls, user):
        next_level = sorted(UserBadges.max_coins_levels + [user.coins_available]).index(user.coins_available)
        if next_level > user.badges.max_coins:
            user.badges.unlock_badge('max_coins', next_level)

    week_points_levels = [499, 999, 2999, 4999]
    @classmethod
    def check_week_points(cls, user):
        week_points = user.points.week_sum()
        next_level = sorted(UserBadges.week_points_levels + [week_points]).index(week_points)
        if next_level > user.badges.week_points:
            user.badges.unlock_badge('week_points', next_level)

    loser_levels = [4, 9, 14, 19]
    @classmethod
    def check_loser(cls, user):
        last_bets = user.bets.last_finished(20)
        if len(last_bets) > 0:
            straight = 0
            for bet in last_bets:
                if user not in (bet.losers() or []):
                    break
                straight += 1
            next_level = sorted(UserBadges.loser_levels + [straight]).index(straight)
            if next_level > user.badges.loser:
                user.badges.unlock_badge("loser", next_level)

    straight_wins_levels = [2, 4, 9, 24]
    @classmethod
    def check_straight_wins(cls, user):
        last_bets = user.bets.last_finished(25)
        if len(last_bets) > 0:
            straight = 0
            for bet in last_bets:
                if user not in (bet.winners() or []):
                    break
                straight += 1
            next_level = sorted(UserBadges.straight_wins_levels + [straight]).index(straight)
            if next_level > user.badges.straight_wins:
                user.badges.unlock_badge("straight_wins", next_level)

    total_wins_levels = [9, 24, 49, 99]
    @classmethod
    def check_total_wins(cls, user):
        total_wins = user.badges.precal_total_wins
        next_level = sorted(UserBadges.total_wins_levels + [total_wins]).index(total_wins)
        if next_level > user.badges.total_wins:
            user.badges.unlock_badge('total_wins', next_level)


class TournamentQuerySet(QuerySet):

    def public(self):
        return self.filter(public=True)

    def private(self):
        return self.filter(public=False)

    def is_author(self, user):
        return self.filter(author=user)

    def is_participant(self, user):
        return self.filter(participants=user)

    def is_allowed(self, user):
        return self.public() | self.is_author(user) | self.is_participant(user)

    def active(self):
        now = timezone.now()
        return self.filter(start__lte=now, end__gte=now)


class TournamentManager(models.Manager):
    use_for_related_fields = True
    
    def get_queryset(self):
        return TournamentQuerySet(self.model, using=self._db)

    def get_clean_queryset(self):
        return TournamentQuerySet(self.model, using=self._db)

    def is_allowed(self, user):
        qs = self.get_queryset()
        return qs.is_allowed(user)


class Tournament(models.Model):
    objects = TournamentManager()
    
    author = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='tournaments_created', blank=True, null=True)
    public = models.BooleanField(blank=True, default=True)
    only_author = models.BooleanField(blank=True, default=True)
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, null=True, related_name='tournaments')
    tag = models.CharField(max_length=255, blank=True, null=True)
    start = models.DateTimeField(blank=True, null=True, default=None)
    end = models.DateTimeField(blank=True, null=True, default=None)
    #reset = models.CharField(max_length=255, blank=True, null=True)
    pic = models.ImageField(upload_to='tournaments', null=True, blank=True)
    title = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True, default="")
    bets = models.ManyToManyField(Bet, blank=True, null=True, related_name='tournaments')

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super(Tournament, self).save(*args, **kwargs)
        if is_new and self.author:
            self.add_participant(self.author)

    @staticmethod
    def check_bet_all_tournaments(bet):
        for t in Tournament.objects.is_allowed(bet.author).active():
            t.check_bet(bet)

    @staticmethod
    def check_bet_bidder_tournaments(bet):
        for t in bet.tournaments.all().active():
            t.add_participant(bet.accepted_bid.author)

    @staticmethod
    def check_bet_participant_tournaments(bet, participant=None):
        for t in bet.tournaments.all().active():
            if participant:
                t.add_participant(participant)
            else:
                t.participants.add(*list(bet.participants()))

    def check_bet(self, bet):
        '''Checks if a bet matches the conditions of
        the tournament and adds it if true'''
        if bet in self.bets.all():
            return False
        if bet.author != self.author and self.only_author:
            #raise GamificationException("Can't add a bet by another author")
            return False
        if self.tag and not self.tag.lower() in bet.title.lower():
            return False
        if not self.public and not bet.author in self.participants.all():
            return False
        self.add_bet(bet)
        if self.public and not bet.is_lottery():
            self.add_participant(bet.author)

    def add_bet(self, bet):
        self.bets.add(bet)

    def add_participant(self, user):
        self.participants.add(user)

    def points(self, user=None):
        qs = UserPoints.objects.filter(bet__tournaments=self)
        if user:
            return qs.user(user)
        else:
            return qs

    def leaderboard(self):
        return self.points().ranking()

    def get_pic_url(self):
        if self.pic:
            return self.pic._get_url()
        else:
            return ""

    def __unicode__(self):
        return self.title or u"No title"


import gamification.signals