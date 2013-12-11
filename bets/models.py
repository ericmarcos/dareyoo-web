import math
from django.db import models
from django.conf import settings
from django_fsm.db.fields import FSMField, transition


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
    odds = models.FloatField(blank=True, null=True, default=0.5)
    accepted_bid = models.ForeignKey("Bid", blank=True, null=True, related_name='accepted')
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True, editable=False)
    bidding_deadline = models.DateTimeField(blank=True, null=True)
    event_deadline = models.DateTimeField(blank=True, null=True)
    public = models.BooleanField(blank=True, default=True)
    recipients = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, null=True)
    claim = models.PositiveSmallIntegerField(blank=True, null=True, choices=BET_CLAIM_CHOICES, default=None)
    claim_lottery_winner = models.ForeignKey("Bid", blank=True, null=True, related_name='winning_bet')
    claim_message = models.TextField(blank=True, null=True, default="")
    points = models.PositiveIntegerField(blank=True, null=True, default=0)
    referee = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='arbitrated_bets', blank=True, null=True, default=None)
    referee_claim = models.PositiveSmallIntegerField(blank=True, null=True, choices=BET_CLAIM_CHOICES, default=None)
    referee_lottery_winner = models.ForeignKey("Bid", blank=True, null=True, related_name='referee_winning_bet')
    log = models.TextField(blank=True, null=True, default="")

    class Meta:
        pass

    def is_simple(self):
        return self.bet_type == TYPE_SIMPLE

    def is_auction(self):
        return self.bet_type == TYPE_AUCTION

    def is_lottery(self):
        return self.bet_type == TYPE_LOTTERY

    def has_bid(self):
        if self.bet_type == TYPE_SIMPLE or self.bet_type == TYPE_AUCTION:
            return self.accepted_bid != None
        elif self.bet_type == TYPE_LOTTERY:
            return sum([len(bid.participants.all()) for bid in self.bids]) > 1

    def pot(self):
        '''
        This is very expensive because it performs many queries
        to the database. Pot should be precalculated.
        '''
        if self.bet_type == TYPE_SIMPLE or self.bet_type == TYPE_AUCTION:
            if self.accepted_bid:
                pot = self.amount + self.accepted_bid.amount
            else:
                pot = self.amount
        if self.bet_type == TYPE_LOTTERY:
            pot = self.amount + sum([bid.amount * len(bid.participants.all()) for bid in self.bids])
        return pot

    def fee(self):
        return math.ceil(self.pot()*settings.FEES_RATIO)*2

    def set_author(self, author):
        author.lock_funds(self.amount + self.referee_escrow)
        author.save()
        self.author = author

    def close(self, arbitrating=False):
        if self.bet_type == TYPE_SIMPLE:
            self.close_simple(arbitrating)
        elif self.bet_type == TYPE_AUCTION:
            self.close_auction(arbitrating)
        elif self.bet_type == TYPE_LOTTERY:
            self.close_lottery(arbitrating)

    def close_simple(self, arbitrating=False):
        claim = self.claim
        if arbitrating:
            claim = self.referee_claim
            if claim == self.claim:
                self.author.unlock_funds(self.referee_escrow)
                self.accepted_bid.author.charge(self.accepted_bid.referee_escrow, locked=True)
            elif claim == self.accepted_bid.claim:
                self.author.charge(self.referee_escrow, locked=True)
                self.accepted_bid.author.unlock_funds(self.accepted_bid.referee_escrow)
            else:
                self.author.unlock_funds(self.referee_escrow / 2)
                self.author.charge(self.referee_escrow / 2, locked=True)
                self.accepted_bid.author.unlock_funds(self.accepted_bid.referee_escrow / 2)
                self.accepted_bid.author.charge(self.accepted_bid.referee_escrow / 2, locked=True)
            self.referee.coins_available += self.referee_escrow
            self.referee.save()
        if claim == CLAIM_NULL:
            self.author.unlock_funds(self.amount)
            self.accepted_bid.author.unlock_funds(self.accepted_bid.amount)
        elif claim == CLAIM_WON:
            self.author.unlock_funds(self.amount)
            self.author.coins_available += self.accepted_bid.amount - self.fee()
            self.accepted_bid.author.charge(self.accepted_bid.amount, locked=True)
        elif claim == CLAIM_LOST:
            self.author.charge(self.amount, locked=True)
            self.accepted_bid.author.unlock_funds(self.accepted_bid.amount)
            self.accepted_bid.author.coins_available += self.amount - self.fee()
        self.author.save()
        self.accepted_bid.author.save()

    def close_auction(self, arbitrating=False):
        '''
        At this point it's the same as the simple bet
        but I keep it in different functions as it might
        change in the future
        '''
        close_simple(arbitrating)

    def close_lottery(self, arbitrating=False):
        self.author.unlock_funds(self.referee_escrow)
        if self.claim == CLAIM_NULL:
            for bid in self.bids.all():
                for p in bid.participants:
                    p.unlock_funds(bid.amount)
        else:
            for bid in self.bids.all():
                if bid.id == self.lottery_winner.id:
                    for p in bid.participants:
                        p.unlock_funds(bid.amount, locked=True)
                else:
                    for p in bid.participants:
                        p.charge(bid.amount, locked=True)
        self.author.save()
        self.accepted_bid.author.save()

    @transition(source='bidding', target='event', save=True, conditions=[has_bid])
    def event(self):
        """
        -Notify users
        """
        pass

    @transition(source='event', target='resolving', save=True)
    def resolving(self):
        """
        -Notify users
        """
        pass

    @transition(source='resolving', target='complaining', save=True)
    def complaining(self):
        """
        -Notify users
        """
        pass

    @transition(source='complaining', target='arbitrating', save=True)
    def arbitrating(self):
        """
        -Notify users
        """
        pass

    @transition(source='bidding', target='closed', save=True)
    def closed_desert(self):
        '''
        -Tornar calers
        '''
        self.author.unlock_funds(self.amount + self.referee_escrow)
        self.author.save()

    @transition(source='complaining', target='closed', save=True)
    def closed_ok(self):
        '''
        -Tornar calers
        -Sumar punts
        '''
        self.close()

    @transition(source='arbitrating', target='closed', save=True)
    def closed_conflict(self):
        '''
        -Tornar calers
        -Sumar punts
        -Gestionar arbitratge
        '''
        self.close(arbitrating=True)
        pass

    def __unicode__(self):
        return self.title


class Bid(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='bids', blank=True, null=True)
    bet = models.ForeignKey(Bet, related_name='bids', blank=True, null=True)
    title = models.CharField(max_length=255, blank=True, null=True)
    amount = models.FloatField(blank=True, null=True)
    referee_escrow = models.FloatField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True, editable=False)
    claim = models.PositiveSmallIntegerField(max_length=63, blank=True, null=True, choices=Bet.BET_CLAIM_CHOICES)
    claim_message = models.TextField(blank=True, null=True, default="")
    points = models.PositiveIntegerField(blank=True, null=True, default=0)
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, null=True)

    def set_author(self, author):
        author.lock_funds(self.amount)
        author.save()
        self.author = author
        self.participants.add(author)

    def add_participant(self, p):
        self.participants.add(p)
        p.lock_funds(self.amount)
        p.save()

    def __unicode__(self):
        return self.title

    class Meta:
        pass
