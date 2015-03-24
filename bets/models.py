import math
import datetime
import warnings
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from django.utils import timezone
from django.db import models
from django.conf import settings
from django.db.models.query import QuerySet
from django.db.models import Sum, Q, F
from django.db.models.aggregates import Count
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django_fsm.db.fields import FSMField, transition
from rest_framework.exceptions import APIException
from celery.execute import send_task
from users.models import *
from users.signals import user_activated
from users.pipelines import unique_slugify


class BetException(APIException):
    status_code = 400

    @property
    def detail(self):
        return str(self)

class BetFactory:

    @staticmethod
    def create(*args, **kwargs):
        t = kwargs.get('bet_type')
        if t:
            t = int(t)
            if t == Bet.TYPE_SIMPLE:
                return BetFactory.create_simple(*args, **kwargs)
            if t == Bet.TYPE_AUCTION:
                return BetFactory.create_auction(*args, **kwargs)
            if t == Bet.TYPE_LOTTERY:
                return BetFactory.create_lottery(*args, **kwargs)
        raise BetException("You must provide a bet_type argument")
    
    @staticmethod
    def create_simple(*args, **kwargs):
        b = Bet(bet_type=Bet.TYPE_SIMPLE,
                title=kwargs.get('title', ""),
                description=kwargs.get('description', ""),
                amount=float(kwargs.get('amount', 1)),
                odds=float(kwargs.get('odds', 2)),
                bidding_deadline=kwargs.get('bidding_deadline', None),
                event_deadline=kwargs.get('event_deadline', timezone.now() + datetime.timedelta(minutes=30)),
                public=kwargs.get('public', True))
        #recipients = kwargs.get('recipients', [])
        b.check_valid()
        #b.referee_escrow = b.referee_fees()
        #b.set_author(kwargs.get('author'))
        #b.save()
        return b

    @staticmethod
    def create_auction(*args, **kwargs):
        b = Bet(bet_type=Bet.TYPE_AUCTION,
                title=kwargs.get('title', ""),
                description=kwargs.get('description', ""),
                amount=kwargs.get('amount', 1),
                bidding_deadline=kwargs.get('bidding_deadline', None),
                event_deadline=kwargs.get('event_deadline', timezone.now() + datetime.timedelta(minutes=30)),
                public=kwargs.get('public', True))
        #        recipients=kwargs.get('recipients', []))
        b.check_valid()
        #b.set_author(author)
        #b.save()
        return b

    @staticmethod
    def create_lottery(*args, **kwargs):
        b = Bet(bet_type=Bet.TYPE_LOTTERY,
                title=kwargs.get('title', ""),
                description=kwargs.get('description', ""),
                amount=kwargs.get('amount', 1),
                bidding_deadline=kwargs.get('bidding_deadline', None),
                event_deadline=kwargs.get('event_deadline', timezone.now() + datetime.timedelta(minutes=30)),
                public=kwargs.get('public', True),
                open_lottery=kwargs.get('open_lottery', True))
        #        recipients=kwargs.get('recipients', []))
        b.check_valid()
        #b.referee_escrow = b.referee_fees()
        #b.set_author(author)
        #b.save()
        return b


class BetQuerySet(QuerySet):
    def tag(self, tag=None):
        if tag:
            return self.filter(title__icontains=tag)
        else:
            return self

    def state(self, bet_state):
        if bet_state and bet_state in dict(Bet.BET_STATE_CHOICES).values():
            return self.filter(bet_state=bet_state)
        else:
            raise BetException('Invalid bet state (valid types: ' + str(dict(Bet.BET_STATE_CHOICES).values()) + ')')

    def bidding(self):
        return self.state('bidding')

    def not_bidding(self):
        return self.exclude(bet_state='bidding')

    def event(self):
        return self.state('event')

    def resolving(self):
        return self.state('resolving')

    def complaining(self):
        return self.state('complaining')

    def arbitrating(self):
        return self.state('arbitrating')

    def closed(self):
        return self.state('closed')

    def open(self):
        return self.exclude(bet_state='closed')

    def type(self, bet_type):
        if bet_type and int(bet_type) in [1, 2, 3]:
            return self.filter(bet_type=bet_type)
        else:
            raise BetException('Invalid bet type (valid types: 1, 2, 3)')

    def simple(self):
        return self.filter(bet_type=1)

    def auction(self):
        return self.filter(bet_type=2)

    def lottery(self):
        return self.filter(bet_type=3)

    def created_by(self, user):
        return self.filter(author=user)

    def bidded_by(self, user):
        return self.filter(bids__author=user)

    def participated_by(self, user):
        return self.filter(bids__participants=user)

    def sent_to(self, user):
        return self.filter(recipients=user)

    def involved(self, user):
        ''' Make sure to add distinct() at the end of your query if you
        use this function '''
        return self.created_by(user) | self.bidded_by(user) | self.participated_by(user) | self.sent_to(user)

    def public(self):
        return self.filter(public=True)

    def following(self, user):
        #TODO: this is very inefficient!
        return self.filter(Q(author__in=list(user.following.all())) & Q(public=True))

    def search_title(self, query):
        return self.filter(title__icontains=query)

    def search_description(self, query):
        return self.filter(description__icontains=query)

    def search(self, query):
        return self.search_title(query) | self.search_description(query)

    def created_between(self, start, end):
        return self.filter(created_at__range=(start, end))

    def created_day(self, prev_days=0):
        today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=-prev_days)
        tomorrow = today + timedelta(hours=24)
        return self.created_between(today, tomorrow)

    def created_week(self, prev_weeks=0):
        today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        monday = today + timedelta(days=-today.weekday(), weeks=-prev_weeks)
        sunday = monday + timedelta(weeks=1) # this is actually next monday
        return self.created_between(monday, sunday)

    def created_month(self, prev_months=0):
        first = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        first = first + relativedelta(months=-prev_months)
        last = first + relativedelta(months=1)
        return self.created_between(first, last)

    def finished_between(self, start, end):
        return self.filter(finished_at__range=(start, end))

    def finished_day(self, prev_days):
        today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=-prev_days)
        tomorrow = today + timedelta(hours=24)
        return self.finished_between(today, tomorrow)

    def finished_week(self, prev_weeks=0):
        today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        monday = today + timedelta(days=-today.weekday(), weeks=-prev_weeks)
        sunday = monday + timedelta(weeks=1) # this is actually next monday
        return self.finished_between(monday, sunday)

    def finished_month(self, prev_months=0):
        first = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        first = first + relativedelta(months=-prev_months)
        last = first + relativedelta(months=1)
        return self.finished_between(first, last)

    def bidding_deadline_missed(self):
        return self.bidding().filter(bidding_deadline__lt=timezone.now())

    def event_deadline_missed(self):
        return self.event().filter(event_deadline__lt=timezone.now())

    def resolving_deadline_missed(self):
        deadline = timezone.now() - timedelta(seconds=settings.RESOLVING_COUNTDOWN)
        return self.resolving().filter(event_deadline__lt=deadline)

    def complaining_deadline_missed(self):
        deadline = timezone.now() - timedelta(seconds=settings.COMPLAINING_COUNTDOWN)
        return self.complaining().filter(resolved_at__lt=deadline)

    def arbitrating_deadline_missed(self):
        deadline = timezone.now() - timedelta(seconds=settings.ARBITRATING_COUNTDOWN)
        return self.arbitrating().filter(complained_at__lt=deadline)

    def fede(self):
        return self.cm('fedebentue')

    def marc(self):
        return self.cm('mcomacast')

    def alfonso(self):
        return self.cm('alfmarpin')

    def cm(self, email):
        return self.filter(Q(author__email__icontains=email) |
            Q(bids__author__email__icontains=email) |
            Q(bids__participants__email__icontains=email))


class BetsManager(models.Manager):
    use_for_related_fields = True

    def get_queryset(self):
        return BetQuerySet(self.model, using=self._db)

    def get_clean_queryset(self):
        return BetQuerySet(self.model, using=self._db)

    def open(self, user):
        qs = self.get_clean_queryset()
        return qs.involved(user) & qs.open()

    def last_finished(self, count = 1):
        qs = self.get_clean_queryset()
        return qs.filter(finished_at__isnull=False).order_by('-finished_at')[0:count]


class Bet(models.Model):
    objects = BetsManager()

    TYPE_SIMPLE  = 1
    TYPE_AUCTION = 2
    TYPE_LOTTERY = 3
    BET_TYPE_CHOICES = ((TYPE_SIMPLE, "simple"),
                        (TYPE_AUCTION, "auction"),
                        (TYPE_LOTTERY, "lottery"))

    STATE_BIDDING     = 1
    STATE_EVENT       = 2
    STATE_RESOLVING   = 3
    STATE_COMPLAINING = 4
    STATE_ARBITRATING = 5
    STATE_CLOSED      = 6
    BET_STATE_CHOICES = ((STATE_BIDDING, "bidding"),
                         (STATE_EVENT, "event"),
                         (STATE_RESOLVING, "resolving"),
                         (STATE_COMPLAINING, "complaining"),
                         (STATE_ARBITRATING, "arbitrating"),
                         (STATE_CLOSED, "closed"))

    CLAIM_WON  = 1
    CLAIM_LOST = 2
    CLAIM_NULL = 3
    BET_CLAIM_CHOICES = ((CLAIM_WON, "won"),
                         (CLAIM_LOST, "lost"),
                         (CLAIM_NULL, "null"))

    BET_LOTTERY_TYPE_CHOICES = (("generic", "Generic"),
                                ("football_result", "Football Result"),
                                ("basketball_result", "Basketball Result"))

    author = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='bets', blank=True, null=True)
    title = models.CharField(max_length=255, blank=True, null=True, default="")
    slug = models.SlugField(max_length=255, blank=True, null=True, default="")
    description = models.TextField(blank=True, null=True, default="")
    tags = models.CharField(max_length=255, blank=True, null=True)
    amount = models.FloatField(blank=True, null=True, default=0)
    referee_escrow = models.FloatField(blank=True, null=True, default=0)
    bet_type = models.PositiveSmallIntegerField(blank=True, null=True, choices=BET_TYPE_CHOICES, default=TYPE_SIMPLE)
    open_lottery = models.BooleanField(blank=True, default=True)
    lottery_type = models.CharField(max_length=255, blank=True, null=True, choices=BET_LOTTERY_TYPE_CHOICES, default="generic")
    bet_state = FSMField(default='bidding')
    odds = models.FloatField(blank=True, null=True, default=2)
    accepted_bid = models.ForeignKey("Bid", blank=True, null=True, related_name='accepted')
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True, editable=False)
    resolved_at = models.DateTimeField(blank=True, null=True, editable=False, default=None)
    complained_at = models.DateTimeField(blank=True, null=True, editable=False, default=None)
    arbitrated_at = models.DateTimeField(blank=True, null=True, editable=False, default=None)
    finished_at = models.DateTimeField(blank=True, null=True, editable=False, default=None)
    bidding_deadline = models.DateTimeField(blank=True, null=True)
    event_deadline = models.DateTimeField(blank=True, null=True)
    public = models.BooleanField(blank=True, default=True)
    recipients = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, null=True)
    claim = models.PositiveSmallIntegerField(blank=True, null=True, choices=BET_CLAIM_CHOICES, default=None)
    claim_lottery_winner = models.ForeignKey("Bid", blank=True, null=True, related_name='winning_bet')
    claim_message = models.TextField(blank=True, null=True, default="")
    referee = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='arbitrated_bets', blank=True, null=True, default=None)
    referee_claim = models.PositiveSmallIntegerField(blank=True, null=True, choices=BET_CLAIM_CHOICES, default=None)
    referee_lottery_winner = models.ForeignKey("Bid", blank=True, null=True, related_name='referee_winning_bet')
    referee_message = models.TextField(blank=True, null=True, default="")
    log = models.TextField(blank=True, null=True, default="")

    _pot = 0

    class Meta:
        pass

    def save(self, *args, **kwargs):
        if not self.pk:
            unique_slugify(self, self.title)
        super(Bet, self).save(*args, **kwargs)

    def get_absolute_url(self, *args, **kwargs):
        return reverse('beta-app-bet-detail', kwargs={'slug': self.slug})

    def check_valid(self):
        if not self.event_deadline:
            raise BetException("You must set an event deadline")
        if self.bidding_deadline and self.bidding_deadline < timezone.now():
            raise BetException("Can't create a bet in the past")
        if self.bidding_deadline and self.bidding_deadline > self.event_deadline - datetime.timedelta(minutes=10):
            raise BetException("The event deadline must be later than the bidding deadline plus 10 minutes")
        if self.amount <= 0:
            raise BetException("The amount must be at least 1")
        if int(self.amount) != self.amount:
            raise BetException("The amount must be an integer value")
        if (self.is_simple() or self.is_auction()) and not (1.2 < self.odds < 51):
            raise BetException("Invalid bet ratio")

    def is_simple(self):
        return self.bet_type == Bet.TYPE_SIMPLE

    def is_auction(self):
        return self.bet_type == Bet.TYPE_AUCTION

    def is_lottery(self):
        return self.bet_type == Bet.TYPE_LOTTERY

    def has_bid(self):
        if self.is_simple() or self.is_auction():
            return self.accepted_bid != None
        elif self.is_lottery():
            return self.n_participants() >= 1

    def has_conflict(self):
        return self.referee != None

    def get_type_name(self):
        return dict(Bet.BET_TYPE_CHOICES).get(self.bet_type)

    def get_state_name(self, state):
        return dict(Bet.BET_STATE_CHOICES).get(state)

    def is_bidding(self):
        return self.bet_state == self.get_state_name(Bet.STATE_BIDDING)

    def is_event(self):
        return self.bet_state == self.get_state_name(Bet.STATE_EVENT)

    def is_resolving(self):
        return self.bet_state == self.get_state_name(Bet.STATE_RESOLVING)

    def is_complaining(self):
        return self.bet_state == self.get_state_name(Bet.STATE_COMPLAINING)

    def is_arbitrating(self):
        return self.bet_state == self.get_state_name(Bet.STATE_ARBITRATING)

    def is_closed(self):
        return self.bet_state == self.get_state_name(Bet.STATE_CLOSED)

    def is_desert(self):
        if self.is_lottery():
            return self.n_participants() == 0
        elif self.is_simple() or self.is_auction():
            return not bool(self.accepted_bid)

    def is_participant(self, user):
        return user in self.participants()

    def lost_conflict(self, user):
        return user in self.conflict_losers()

    def conflict_losers(self):
        losers = []
        if self.is_closed() and self.has_conflict():
            if self.is_lottery():
                if self.claim_lottery_winner != self.referee_lottery_winner and self.claim != self.referee_claim:
                    losers.append(self.author)
                bid_conflicted = self.bids.filter(claim_author__isnull=False).first()
                if bid_conflicted and bid_conflicted != self.referee_lottery_winner and bid_conflicted.claim != self.referee_claim:
                    losers.append(bid_conflicted.claim_author)
            else:
                if self.claim != self.referee_claim:
                    losers.append(self.author)
                if self.accepted_bid.claim != self.referee_claim:
                    losers.append(self.accepted_bid.author)
        return losers

    def invite(self, invites):
        if invites and len(invites) > 0:
            recipients = []
            for invite in invites:
                u = DareyooUser.objects.filter(username=invite)
                if len(u) == 0:
                    u = DareyooUser.objects.filter(email=invite)
                if len(u) == 0:
                    try:
                        validate_email(invite)
                        user = DareyooUser(email=invite)
                        user.reference_user = self.author
                        user.save()
                        u = [user]
                    except ValidationError as e:
                        pass
                if len(u) > 0:
                    recipients.append(u[0])
            self.recipients = recipients
            #TODO: remove dependency of notifications app using a signal
            send_task('send_invite_notifications', [self.id])

    def participants(self):
        if self.is_simple() or self.is_auction():
            if self.accepted_bid:
                return set([self.author, self.accepted_bid.author])
            else:
                return set([self.author])
        elif self.is_lottery():
            return set(u for b in self.bids.all() for u in b.participants.all())

    def n_participants(self):
        if self.is_simple() or self.is_auction():
            return 2 if self.accepted_bid else 1
        elif self.is_lottery():
            return DareyooUser.objects.filter(participated_bids__bet=self).count()

    def pot(self):
        '''
        TODO: This is very expensive because it performs many queries
        to the database. Pot should be precalculated.
        '''
        if self._pot:
            return self._pot
        if self.is_simple():
            pot = math.ceil(self.amount*self.odds)
        if self.is_auction():
            if self.accepted_bid:
                pot = self.amount + self.accepted_bid.amount
            else:
                pot = self.amount
        if self.is_lottery():
            pot = sum([bid.amount * bid.participants.count() for bid in self.bids.all()])
        return pot

    def winners(self):
        if (self.is_complaining() or self.is_arbitrating() or self.is_closed()) and not self.is_desert():
            claim = self.referee_claim or self.claim
            if self.is_lottery():
                if claim != Bet.CLAIM_NULL:
                    bid = self.referee_lottery_winner or self.claim_lottery_winner
                    return list(bid.participants.all()) if bid else None
            else:
                if claim == Bet.CLAIM_NULL:
                    return None
                elif claim == Bet.CLAIM_WON:
                    return (self.author,)
                else:
                    return (self.accepted_bid.author,) if self.accepted_bid else None
        return None

    def losers(self):
        if self.is_closed() and not self.is_desert():
            if self.is_lottery():
                bid = self.referee_lottery_winner or self.claim_lottery_winner
                return [user for b in self.bids.all() for user in b.participants.all() if b != bid]
            else:
                claim = self.referee_claim or self.claim
                if claim == Bet.CLAIM_NULL:
                    return None
                elif claim == Bet.CLAIM_LOST:
                    return (self.author,)
                else:
                    return (self.accepted_bid.author,)
        return None

    def winning_fees(self):
        return math.ceil(self.pot()*settings.WINNING_FEES_RATIO)

    def referee_fees(self):
        return math.ceil(self.pot()*settings.REFEREE_FEES_RATIO)*2

    def set_author(self, author):
        if author:
            if self.is_simple() or self.is_auction():
                author.lock_funds(self.amount)
                author.save()
            self.author = author
            user_activated.send(sender=self.__class__, user=author, level=3)
        else:
            raise BetException("Author can't be None")

    def add_bid(self, bid, user, auto_participate=False):
        auction_bid_limit = 3
        if self.is_bidding():
            #TODO: think if we should limit the number of bids per user per bet.
            #I'm not doing it now because of the lottery use case: a singe user
            #(for example, the bet creator) can add many bids
            # UPDATE: currently set at 3 bids per user
            if self.is_auction() and self.bids.all().created_by(user).count() >= auction_bid_limit:
                raise BetException("Can't post more than %s bids per bet per user" % auction_bid_limit)
            if self.is_lottery() and self.open_lottery and user.id != self.author.id and self.bids.all().created_by(user).count() >= 1:
                raise BetException("Can't post more than result bet per user")
            if self.is_lottery() and not self.open_lottery and user.id != self.author.id:
                raise BetException("Only the bet author can post results in a closed lottery")
            if not self.is_lottery() and self.author.id == user.id:
                raise BetException("Can't play against yourself!")
            if not self.public and self.recipients.filter(id=user.id).count() == 0 and user != self.author:
                raise BetException("Can't bid on a private bet if you're not invited.")
            bid.bet = self
            bid.set_author(user)
            if self.is_simple():
                bid.amount = self.pot() - self.amount
            elif self.is_lottery():
                bid.amount = self.amount
            bid.check_valid()
            bid.save()
            user_activated.send(sender=self.__class__, user=user, level=2)
            if self.is_simple():
                self.accept_bid(bid.id)
            if self.is_lottery() and auto_participate:
                bid.add_participant(user)
        else:
            raise BetException("Can't add a bid to this bet because it's not on bidding sate (current state:%s)" % self.bet_state)

    def remove_bid(self, bid_id):
        if self.is_bidding():
            bid = Bid.objects.get(id=bid_id)
            if bid_id in [b.id for b in self.bids.all()]:
                if self.is_lottery():
                    for p in bid.participants.all():
                        p.unlock_funds(bid.amount)
                        p.save()
                bid.delete()
                user_activated.send(sender=self.__class__, user=self.author, level=2)
        else:
            raise BetException("Can't remove a bid from this bet because it's not on bidding sate (current state:%s)" % self.bet_state)
    
    def merge_bids(self):
        for b1 in self.bids.all():
            for b2 in self.bids.all():
                try:
                    if b1 != b2 and b1.title.replace(" ", "") == b2.title.replace(" ", ""):
                        b1.participants.add(*list(b2.participants.all()))
                        b2.delete()
                except:
                    pass

    def get_top_voted_results(self):
        if self.lottery_type and "result" in self.lottery_type:
            return self.bids.all().annotate(np=Count('participants')).order_by('-np')[:3]
        else:
            return self.bids.all()

    def accept_bet(self, user):
        if self.is_bidding():
            if self.is_simple():
                bid = Bid()
                self.add_bid(bid, user)
                user_activated.send(sender=self.__class__, user=user, level=2)
            else:
                raise BetException("Can't accept this bet because it's not of 'basic' type.")
        else:
            raise BetException("Can't accept this bet because it's not on bidding sate (current state:%s)" % self.bet_state)

    def accept_bid(self, bid_id):
        if self.is_bidding():
            if self.is_lottery():
                raise BetException("Can't accept bid: operation not permited for lotteries")
            if not self.bids.filter(id=bid_id).exists():
                raise BetException("Can't accept bid: invalid id")
            self.accepted_bid_id = bid_id
            if self.is_auction():
                self.odds = float(self.amount + self.accepted_bid.amount) / self.amount
            self.check_valid()
            self.accepted_bid.author.lock_funds(self.accepted_bid.amount)
            self.accepted_bid.author.save()
            self.event()
            user_activated.send(sender=self.__class__, user=self.author, level=2)
        else:
            raise BetException("Can't accept a bid from this bet because it's not on bidding sate (current state:%s)" % self.bet_state)

    def resolve(self, claim=None, claim_lottery_winner=None, claim_message=""):
        if self.is_event():
            self.bet_state = 'resolving'
        if self.is_resolving():
            if self.is_simple() or self.is_auction():
                if claim in dict(Bet.BET_CLAIM_CHOICES).keys():
                    self.claim = claim
                    self.claim_message = claim_message
                else:
                    raise BetException("Invalid claim")
            if self.is_lottery():
                if claim == None and self.bids.filter(id=claim_lottery_winner).count() > 0:
                    self.claim_lottery_winner_id = claim_lottery_winner
                    self.claim_message = claim_message
                elif claim == Bet.CLAIM_NULL:
                    self.claim = Bet.CLAIM_NULL
                    self.claim_message = claim_message
                else:
                    raise BetException("Invalid claim")
            self.resolved_at = timezone.now()
            user_activated.send(sender=self.__class__, user=self.author, level=2)
        else:
            raise BetException("Can't claim on a bet that is not in resolving state (current state: %s)" % self.bet_state)

    def arbitrate(self, user, claim=None, claim_lottery_winner=None, claim_message=""):
        if self.is_participant(user):
            raise BetException("A bet can't be arbitrated by one of its participants")
        if self.is_arbitrating():
            self.referee_message = claim_message
            self.referee = user
            if self.is_simple() or self.is_auction():
                if claim in dict(Bet.BET_CLAIM_CHOICES).keys():
                    self.referee_claim = claim
                else:
                    raise BetException("Invalid claim")
            if self.is_lottery():
                if claim == None and self.bids.filter(id=claim_lottery_winner).exists():
                    self.referee_lottery_winner_id = int(claim_lottery_winner)
                elif claim == Bet.CLAIM_NULL:
                    self.referee_claim = Bet.CLAIM_NULL
                else:
                    raise BetException("Invalid claim")
            self.arbitrated_at = timezone.now()
            user_activated.send(sender=self.__class__, user=user, level=2)
        else:
            raise BetException("Can't arbitrate on a bet that is not in arbitrating state (current state: %s)" % self.bet_state)

    def close(self, arbitrating=False):
        if self.is_desert():
            if self.is_simple() or self.is_auction():
                self.author.unlock_funds(self.amount)
            self.author.unlock_funds(self.referee_escrow)
            self.author.save()
        else:
            if self.is_simple():
                self.close_simple(arbitrating)
            elif self.is_auction():
                self.close_auction(arbitrating)
            elif self.is_lottery():
                self.close_lottery(arbitrating)
        self.finished_at = timezone.now()

    def close_simple(self, arbitrating=False):
        claim = self.claim
        if arbitrating:
            claim = self.referee_claim
            if claim == self.claim:
                self.accepted_bid.author.charge(self.referee_escrow, ignore_negative=True)
            elif claim == self.accepted_bid.claim:
                self.author.charge(self.referee_escrow, ignore_negative=True)
            else:
                self.author.charge(self.referee_escrow / 2, ignore_negative=True)
                self.accepted_bid.author.charge(self.referee_escrow / 2, ignore_negative=True)
            if self.referee:
                self.referee.coins_available += self.referee_escrow
                self.referee.save()
        if claim == Bet.CLAIM_NULL:
            self.author.unlock_funds(self.amount)
            self.accepted_bid.author.unlock_funds(self.accepted_bid.amount)
        elif claim == Bet.CLAIM_WON:
            self.author.unlock_funds(self.amount)
            self.author.coins_available += self.accepted_bid.amount - self.winning_fees()
            self.accepted_bid.author.charge(self.accepted_bid.amount, locked=True)
        elif claim == Bet.CLAIM_LOST:
            self.author.charge(self.amount, locked=True)
            self.accepted_bid.author.unlock_funds(self.accepted_bid.amount)
            self.accepted_bid.author.coins_available += self.amount - self.winning_fees()
        self.author.save()
        self.accepted_bid.author.save()

    def close_auction(self, arbitrating=False):
        '''
        At this point it's the same as the simple bet
        but I keep it in different functions as it might
        change in the future
        '''
        self.close_simple(arbitrating)

    def close_lottery(self, arbitrating=False):
        claim = self.claim
        winner = self.claim_lottery_winner
        for p in self.participants():
            p.coins_locked = max(p.coins_locked, self.amount)
            p.save()
        if arbitrating:
            claim = self.referee_claim
            winner = self.referee_lottery_winner
            complainer = next(bid for bid in self.bids.all() if bid.claim != None)
            if claim == self.claim or winner == self.claim_lottery_winner:
                complainer.claim_author.charge(self.referee_escrow, ignore_negative=True)
            elif claim == complainer.claim or winner == complainer:
                self.author.charge(self.referee_escrow, ignore_negative=True)
            else:
                self.author.charge(self.referee_escrow / 2, ignore_negative=True)
                complainer.claim_author.charge(self.referee_escrow / 2, ignore_negative=True)
            if self.referee:
                self.referee.coins_available += self.referee_escrow
                self.referee.save()
        if claim == Bet.CLAIM_NULL:
            for bid in self.bids.all():
                for p in bid.participants.all():
                    p.unlock_funds(bid.amount)
                    p.save()
        elif winner:
            n = winner.participants.count() or 1
            price = math.ceil((self.pot() - self.winning_fees()) / n)
            for bid in self.bids.all():
                if bid.id != winner.id:
                    for p in bid.participants.all():
                        p.charge(bid.amount, locked=True)
                        p.save()
            for p in winner.participants.all():
                p.charge(winner.amount, locked=True)
                p.coins_available += price
                p.save()
        else:
            warnings.warn("Closing a lottery whose claim is different than NULL and has no claim_lottery_winner... shouldn't get here!")

    @transition(field=bet_state, source='bidding', target='event', save=True, conditions=[has_bid])
    def event(self):
       pass

    @transition(field=bet_state, source='event', target='resolving', save=True)
    def resolving(self):
        pass

    @transition(field=bet_state, source='resolving', target='complaining', save=True)
    def complaining(self):
        pass

    @transition(field=bet_state, source='complaining', target='arbitrating', save=True)
    def arbitrating(self):
        pass

    @transition(field=bet_state, source='bidding', target='closed', save=True)
    def closed_desert(self):
        self.close()

    @transition(field=bet_state, source='complaining', target='closed', save=True)
    def closed_ok(self):
        self.close()

    @transition(field=bet_state, source='arbitrating', target='closed', save=True)
    def closed_conflict(self):
        self.close(arbitrating=True)

    def next_state(self):
        if self.is_bidding():
            if self.is_desert():
                self.closed_desert()
            else:
                self.event()
        elif self.is_event():
            self.resolving()
        elif self.is_resolving():
            if not self.claim:
                if self.is_lottery():
                    self.claim = Bet.CLAIM_NULL
                else:
                    self.claim = Bet.CLAIM_LOST
                self.resolved_at = timezone.now()
            self.complaining()
        elif self.is_complaining():
            if Bid.objects.filter(bet=self, claim__isnull=False).count() == 0:
                self.closed_ok()
            else:
                self.arbitrating()
        elif self.is_arbitrating():
            self.closed_conflict()

    def __unicode__(self):
        if self.title:
            return unicode(self.id) + " - " + unicode(self.title)
        return unicode(self.title) or unicode(self.id) or u"Bet object"


class BidQuerySet(QuerySet):
    def tag(self, tag=None):
        if tag:
            return self.filter(title__icontains=tag)
        else:
            return self

    def created_by(self, user):
        return self.filter(author=user)

    def participated_by(self, user):
        return self.filter(participants=user)

    def involved(self, user):
        ''' Make sure to add distinct() at the end of your query if you
        use this function '''
        return self.created_by(user) | self.participated_by(user)

    def search_title(self, query):
        return self.filter(title__icontains=query)

    def search(self, query):
        return self.search_title(query)


class BidsManager(models.Manager):
    use_for_related_fields = True

    def get_queryset(self):
        return BidQuerySet(self.model, using=self._db)

    def get_clean_queryset(self):
        return BidQuerySet(self.model, using=self._db)


class Bid(models.Model):
    objects = BidsManager()

    author = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='bids', blank=True, null=True)
    bet = models.ForeignKey(Bet, related_name='bids', blank=True, null=True)
    title = models.CharField(max_length=255, blank=True, null=True)
    amount = models.FloatField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True, editable=False)
    claim = models.PositiveSmallIntegerField(max_length=63, blank=True, null=True, choices=Bet.BET_CLAIM_CHOICES)
    claim_message = models.TextField(blank=True, null=True, default="")
    claim_author = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='lottery_claimer', blank=True, null=True)
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='participated_bids', blank=True, null=True)
    pic = models.ImageField(upload_to='bids', null=True, blank=True)

    def check_valid(self):
        if self.amount <= 0:
            raise BetException("The amount must be at least 1")
        if int(self.amount) != self.amount:
            raise BetException("The amount must be an integer value")

    def set_author(self, author):
        self.author = author

    def add_participant(self, p):
        if self.bet.is_lottery():
            if not self.bet.public and self.bet.recipients.filter(id=p.id).count() == 0 and p != self.bet.author:
                raise BetException("Can't participate on a private bet if you're not invited.")
            if p in self.bet.participants():
                raise BetException("Can't participate in more than one option in a lottery")
            p.lock_funds(self.amount)
            p.save()
        self.participants.add(p)
        user_activated.send(sender=self.__class__, user=p, level=2)

    def complain(self, user, claim=None, claim_message=""):
        if not self.bet.is_participant(user):
            raise BetException("Only a participant of a bet can complain about it")
        if user == self.bet.author:
            raise BetException("The author of the bet can't complain about it")
        if self.bet.is_complaining():
            if claim in dict(Bet.BET_CLAIM_CHOICES).keys() and claim != self.bet.claim:
                self.claim = claim
                self.claim_message = claim_message
                self.claim_author = user
                self.bet.referee_escrow = self.bet.referee_fees()
                self.bet.complained_at = timezone.now()
                self.bet.save()
                user_activated.send(sender=self.__class__, user=user, level=2)
            else:
                raise BetException("Invalid claim")
        else:
            raise BetException("Can't complain on a bet that is not in complaining state (current state: %s)" % self.bet.bet_state)

    def get_pic_url(self):
        if self.pic:
            return self.pic._get_url()
        else:
            return ""

    def __unicode__(self):
        return unicode(self.title) or unicode(self.id) or u"Bid object"

    class Meta:
        pass


class BetChoice(models.Model):
    bet = models.ForeignKey(Bet, related_name='choices', blank=True, null=True)
    title = models.CharField(max_length=255, blank=True, null=True)
    pic = models.ImageField(upload_to='bet_choices', null=True, blank=True)

    def get_pic_url(self):
        if self.pic:
            return self.pic._get_url()
        else:
            return ""


import bets.signals