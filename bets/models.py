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
    title = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    tags = models.CharField(max_length=255, blank=True, null=True)
    amount = models.FloatField(blank=True, null=True)
    referee_escrow = models.FloatField(blank=True, null=True)
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
    claim_message = models.TextField(blank=True, null=True, default="")
    points = models.PositiveIntegerField(blank=True, null=True, default=0)
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
        return self.accepted_bid != None

    def set_author(self, author):
        author.lock_funds(self.amount + self.referee_escrow)
        author.save()
        self.author = author

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

    @transition(source=('bidding'), target='closed', save=True)
    def closed_desert(self):
        '''
        -Tornar calers
        '''
        pass

    @transition(source=('complaining'), target='closed', save=True)
    def closed_ok(self):
        '''
        -Tornar calers
        -Sumar punts
        '''
        pass

    @transition(source=('arbitrating'), target='closed', save=True)
    def closed_conflict(self):
        '''
        -Tornar calers
        -Sumar punts
        -Gestionar arbitratge
        '''
        pass

    def bidding_deadline(self):
        if self.has_bid():
            self.event()
        else:
            self.closed_desert()

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

    def __unicode__(self):
        return self.title

    class Meta:
        pass
