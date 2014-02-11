import math
import datetime
import warnings
from django.utils import timezone
from django.db import models
from django.conf import settings
from django_fsm.db.fields import FSMField, transition
from rest_framework.exceptions import APIException


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
                amount=int(kwargs.get('amount', 1)),
                odds=int(kwargs.get('odds', 2)),
                bidding_deadline=kwargs.get('bidding_deadline', timezone.now() + datetime.timedelta(minutes=10)),
                event_deadline=kwargs.get('event_deadline', timezone.now() + datetime.timedelta(minutes=30)),
                public=kwargs.get('public', True))
        #recipients = kwargs.get('recipients', [])
        b.check_valid()
        b.referee_escrow = b.referee_fees()
        #b.set_author(kwargs.get('author'))
        #b.save()
        return b

    @staticmethod
    def create_auction(*args, **kwargs):
        b = Bet(bet_type=Bet.TYPE_AUCTION,
                title=kwargs.get('title', ""),
                description=kwargs.get('description', ""),
                amount=kwargs.get('amount', 1),
                bidding_deadline=kwargs.get('bidding_deadline', timezone.now() + datetime.timedelta(minutes=10)),
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
                bidding_deadline=kwargs.get('bidding_deadline', timezone.now() + datetime.timedelta(minutes=10)),
                event_deadline=kwargs.get('event_deadline', timezone.now() + datetime.timedelta(minutes=30)),
                public=kwargs.get('public', True))
        #        recipients=kwargs.get('recipients', []))
        b.check_valid()
        b.referee_escrow = b.referee_fees()
        #b.set_author(author)
        #b.save()
        return b

class Bet(models.Model):
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

    author = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='bets', blank=True, null=True)
    title = models.CharField(max_length=255, blank=True, null=True, default="")
    description = models.TextField(blank=True, null=True, default="")
    tags = models.CharField(max_length=255, blank=True, null=True)
    amount = models.FloatField(blank=True, null=True, default=0)
    referee_escrow = models.FloatField(blank=True, null=True, default=0)
    bet_type = models.PositiveSmallIntegerField(blank=True, null=True, choices=BET_TYPE_CHOICES, default=TYPE_SIMPLE)
    bet_state = FSMField(default='bidding')
    odds = models.FloatField(blank=True, null=True, default=2)
    accepted_bid = models.ForeignKey("Bid", blank=True, null=True, related_name='accepted')
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True, editable=False)
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
    log = models.TextField(blank=True, null=True, default="")

    class Meta:
        pass

    def check_valid(self):
        if not self.bidding_deadline or not self.event_deadline:
            raise BetException("You must set a bidding deadline and an event deadline")
        if self.bidding_deadline < timezone.now():
            raise BetException("Can't create a bet in the past")
        if self.bidding_deadline > self.event_deadline - datetime.timedelta(minutes=10):
            raise BetException("The event deadline must be later than the bidding deadline plus 10 minutes")

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
            return sum([len(bid.participants.all()) for bid in self.bids.all()]) > 1

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

    def is_participant(self, user):
        if self.is_simple() or self.is_auction():
            if self.accepted_bid:
                return user == self.author or user == self.accepted_bid.author
            else:
                return user == self.author
        elif self.is_lottery():
            return user.id in [u.id for b in self.bids.all() for u in b.participants.all()]

    def pot(self):
        '''
        This is very expensive because it performs many queries
        to the database. Pot should be precalculated.
        '''
        if self.is_simple():
            pot = math.ceil(self.amount*self.odds)
        if self.is_auction():
            if self.accepted_bid:
                pot = self.amount + self.accepted_bid.amount
            else:
                pot = self.amount
        if self.is_lottery():
            pot = sum([bid.amount * len(bid.participants.all()) for bid in self.bids.all()])
        return pot

    def winners(self):
        if self.is_closed():
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

    def losers(self):
        if self.is_closed():
            if self.is_lottery():
                bid = self.referee_lottery_winner or self.claim_lottery_winner
                return [user for b in self.bids.all() for user in b.participants.all() if b != bid]
            else:
                claim = self.referee_claim or self.claim_author
                if claim == Bet.CLAIM_NULL:
                    return None
                elif claim == Bet.CLAIM_LOST:
                    return (self.author,)
                else:
                    return (self.accepted_bid.author,)

    def winning_fees(self):
        return math.ceil(self.pot()*settings.WINNING_FEES_RATIO)

    def referee_fees(self):
        if self.is_lottery():
            return settings.LOTTERY_REFEREE_FEES
        return math.ceil(self.pot()*settings.REFEREE_FEES_RATIO)*2

    def set_author(self, author):
        if author:
            if self.is_simple():
                author.lock_funds(self.amount + self.referee_escrow)
            elif self.is_auction():
                author.lock_funds(self.amount)
            elif self.is_lottery():
                author.lock_funds(self.referee_escrow)
            author.save()
            self.author = author
        else:
            raise BetException("Author can't be None")

    def add_bid(self, bid, user):
        if self.is_bidding():
            #TODO: think if we should limit the number of bids per user per bet.
            #I'm not doing it now because of the lottery use case: a singe user
            #(for example, the bet creator) can add many bids
            bid.bet = self
            bid.set_author(user)
            if self.is_simple():
                bid.amount = self.pot() - self.amount
            elif self.is_lottery():
                bid.amount = self.amount
            bid.save()
            if self.is_simple():
                self.accept_bid(bid.id)
        else:
            raise BetException("Can't add a bid to this bet because it's not on bidding sate (current state:%s)" % self.bet_state)

    def remove_bid(self, bid_id):
        if self.is_bidding():
            bid = Bid.objects.get(id=bid_id)
            if bid_id in [b.id for b in self.bids.all()]:
                if self.is_lottery():
                    for p in bid.participants.all():
                        p.unlock_funds(bid.amount)
                bid.delete()
        else:
            raise BetException("Can't remove a bid from this bet because it's not on bidding sate (current state:%s)" % self.bet_state)

    def accept_bet(self, user):
        if self.is_bidding():
            if self.is_simple():
                bid = Bid()
                self.add_bid(bid, user)
            else:
                raise BetException("Can't accept this bet because it's not of 'simple' type.")
        else:
            raise BetException("Can't accept this bet because it's not on bidding sate (current state:%s)" % self.bet_state)

    def accept_bid(self, bid_id):
        if self.is_bidding():
            if self.is_lottery():
                raise BetException("Can't accept bid: operation not permited for lotteries")
            if not bid_id in [b.id for b in self.bids.all()]:
                raise BetException("Can't accept bid: invalid id")
            self.accepted_bid_id = bid_id
            if self.is_auction():
                self.referee_escrow = self.referee_fees()
                self.author.lock_funds(self.referee_escrow)
                self.author.save()
            self.accepted_bid.author.lock_funds(self.accepted_bid.amount)
            self.accepted_bid.author.save()
            self.event()
        else:
            raise BetException("Can't accept a bid from this bet because it's not on bidding sate (current state:%s)" % self.bet_state)

    def resolve(self, claim=None, claim_lottery_winner=None, claim_message=""):
        if self.is_resolving():
            if self.is_simple() or self.is_auction():
                if claim in dict(Bet.BET_CLAIM_CHOICES).keys():
                    self.claim = claim
                    self.claim_message = claim_message
                else:
                    raise BetException("Invalid claim")
            if self.is_lottery():
                if claim == None and claim_lottery_winner in [b.id for b in self.bids.all()]:
                    self.claim_lottery_winner = claim_lottery_winner
                    self.claim_message = claim_message
                elif claim == Bet.CLAIM_NULL:
                    self.claim = Bet.CLAIM_NULL
                else:
                    raise BetException("Invalid claim")
        else:
            raise BetException("Can't claim on a bet that is not in resolving state (current state: %s)" % self.bet_state)

    def arbitrate(self, user, claim=None, claim_lottery_winner=None, claim_message=""):
        if self.is_participant(user):
            raise BetException("A bet can't be arbitrated by one of its participants")
        if self.is_arbitrating():
            self.claim_message = claim_message
            self.referee = user
            if self.is_simple() or self.is_auction():
                if claim in dict(Bet.BET_CLAIM_CHOICES).keys():
                    self.referee_claim = claim
                else:
                    raise BetException("Invalid claim")
            if self.is_lottery():
                if claim == None and claim_lottery_winner in [b.id for b in self.bids.all()]:
                    self.claim_lottery_winner = claim_lottery_winner
                elif claim == Bet.CLAIM_NULL:
                    self.claim = Bet.CLAIM_NULL
                else:
                    raise BetException("Invalid claim")
        else:
            raise BetException("Can't arbitrate on a bet that is not in arbitrating state (current state: %s)" % self.bet_state)

    def close(self, arbitrating=False):
        if self.is_simple():
            self.close_simple(arbitrating)
        elif self.is_auction():
            self.close_auction(arbitrating)
        elif self.is_lottery():
            self.close_lottery(arbitrating)

    def close_simple(self, arbitrating=False):
        claim = self.claim
        if arbitrating:
            claim = self.referee_claim
            if claim == self.claim:
                self.author.unlock_funds(self.referee_escrow)
                self.accepted_bid.author.charge(self.referee_escrow, locked=True)
            elif claim == self.accepted_bid.claim:
                self.author.charge(self.referee_escrow, locked=True)
                self.accepted_bid.author.unlock_funds(self.referee_escrow)
            else:
                self.author.unlock_funds(self.referee_escrow / 2)
                self.author.charge(self.referee_escrow / 2, locked=True)
                self.accepted_bid.author.unlock_funds(self.referee_escrow / 2)
                self.accepted_bid.author.charge(self.referee_escrow / 2, locked=True)
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
        if arbitrating:
            claim = self.referee_claim
            winner = self.referee_lottery_winner
            complainer = next(bid for bid in self.bids if bid.claim != None)
            if claim == self.claim or winner == self.claim_lottery_winner:
                self.author.unlock_funds(self.referee_escrow)
                complainer.claim_author.charge(self.referee_escrow, locked=True)
            elif claim == complainer.claim or winner == complainer:
                self.author.charge(self.referee_escrow, locked=True)
                complainer.claim_author.unlock_funds(self.referee_escrow)
            else:
                self.author.unlock_funds(self.referee_escrow / 2)
                self.author.charge(self.referee_escrow / 2, locked=True)
                complainer.claim_author.unlock_funds(self.referee_escrow / 2)
                complainer.claim_author.charge(self.referee_escrow / 2, locked=True)
            self.referee.coins_available += self.referee_escrow
            self.referee.save()
        if claim == Bet.CLAIM_NULL:
            for bid in self.bids.all():
                for p in bid.participants.all():
                    p.unlock_funds(bid.amount)
                    p.save()
        elif winner:
            price = math.ceil((self.pot() - self.winning_fees()) / len(winner.participants.all()))
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
        '''
        -Tornar calers
        '''
        self.author.unlock_funds(self.amount + self.referee_escrow)
        self.author.save()

    @transition(field=bet_state, source='complaining', target='closed', save=True)
    def closed_ok(self):
        '''
        -Tornar calers
        -Sumar punts
        '''
        self.close()

    @transition(field=bet_state, source='arbitrating', target='closed', save=True)
    def closed_conflict(self):
        '''
        -Tornar calers
        -Sumar punts
        -Gestionar arbitratge
        '''
        self.close(arbitrating=True)

    def __unicode__(self):
        return self.title


class Bid(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='bids', blank=True, null=True)
    bet = models.ForeignKey(Bet, related_name='bids', blank=True, null=True)
    title = models.CharField(max_length=255, blank=True, null=True)
    amount = models.FloatField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True, editable=False)
    claim = models.PositiveSmallIntegerField(max_length=63, blank=True, null=True, choices=Bet.BET_CLAIM_CHOICES)
    claim_message = models.TextField(blank=True, null=True, default="")
    claim_author = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='lottery_claimer', blank=True, null=True)
    points = models.PositiveIntegerField(blank=True, null=True, default=0)
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, null=True)

    def set_author(self, author):
        self.author = author

    def add_participant(self, p):
        self.participants.add(p)
        if self.is_lottery():
            p.lock_funds(self.amount)
            p.save()

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
                user.lock_funds(self.bet.referee_escrow)
                user.save()
            else:
                raise BetException("Invalid claim")
        else:
            raise BetException("Can't complain on a bet that is not in complaining state (current state: %s)" % self.bet.bet_state)

    def __unicode__(self):
        return self.title

    class Meta:
        pass


import bets.signals