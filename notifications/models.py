from django.db import models
from django.conf import settings
from bets.models import Bet


class NotificationFactory:

    @staticmethod
    def new_follower(recipient, user, *args, **kwargs):
        n = Notification()
        n.recipient = recipient
        n.notification_type = Notification.TYPE_NEW_FOLLOWER
        n.subject = "%s started following you." % user
        n.user = user
        return n

    @staticmethod
    def bet_received(recipient, bet, *args, **kwargs):
        n = Notification()
        n.recipient = recipient
        n.notification_type = Notification.TYPE_BET_RECEIVED
        n.subject = "%s sent you a bet! \"%s\"" % (bet.author.username, bet.title)
        n.bet = bet
        return n

    @staticmethod
    def bet_accepted(bet):
        n = Notification()
        n.recipient = bet.author
        n.notification_type = Notification.TYPE_BET_ACCEPTED
        n.subject = "%s accepted your bet \"%s\"" % (bet.accepted_bid.author, bet.title)
        n.bet = bet
        n.user = bet.accepted_bid.author
        return n

    @staticmethod
    def bid_posted(bid):
        n = Notification()
        n.recipient = bid.bet.author
        n.notification_type = Notification.TYPE_BID_POSTED
        n.subject = "%s posted a bid on your bet \"%s\"" % (bid.author, bid.bet.title)
        n.bet = bid.bet
        n.user = bid.author
        return n

    @staticmethod
    def bid_accepted(bid):
        n = Notification()
        n.recipient = bid.author
        n.notification_type = Notification.TYPE_BID_ACCEPTED
        n.subject = "%s accepted your bid on the bet \"%s\"" % (bid.bet.author.username, bid.bet.title)
        n.bet = bid.bet
        return n

    @staticmethod
    def bet_event_finished(bet):
        n = Notification()
        n.recipient = bet.author
        n.notification_type = Notification.TYPE_BET_EVENT_FINISHED
        n.subject = "Your bet finished! You have 24h to resolve it."
        n.bet = bet
        return n

    @staticmethod
    def bet_resolving_finished(bet, recipient=None):
        n = Notification()
        if bet.is_simple() or bet.is_auction():
            n.recipient = bet.accepted_bid.author
            if bet.claim == Bet.CLAIM_WON:
                n.notification_type = Notification.TYPE_BET_RESOLVING_FINISHED_AUTHOR_WON
                n.subject = "Ouch! You lost %s's bet \"%s\". You have 24h to complain." % (bet.author.username, bet.title)
            elif bet.claim == Bet.CLAIM_LOST:
                n.notification_type = Notification.TYPE_BET_RESOLVING_FINISHED_AUTHOR_LOST
                n.subject = "Yay! You won %s's bet \"%s\". If you want, you have 24h to complain." % (bet.author.username, bet.title)
            elif bet.claim == Bet.CLAIM_NULL:
                n.notification_type = Notification.TYPE_BET_RESOLVING_FINISHED_NULL
                n.subject = "%s's bet \"%s\" was declared null. You have 24h to complain." % (bet.author.username, bet.title)
            if bet.claim_message:
                n.subject = bet.claim_message
        elif bet.is_lottery():
            n.recipient = recipient
            if bet.claim == Bet.CLAIM_NULL:
                n.notification_type = Notification.TYPE_BET_RESOLVING_FINISHED_NULL
                n.subject = "%s's lottery \"%s\" was declared null. You have 24h to complain." % (bet.author.username, bet.title)
            elif recipient in [bet.claim_lottery_winner.participants.all()]:
                n.notification_type = Notification.TYPE_BET_RESOLVING_FINISHED_AUTHOR_LOST
                n.subject = "Yay! You won %s's lottery \"%s\"." % (bet.author.username, bet.title)
            else:
                n.notification_type = Notification.TYPE_BET_RESOLVING_FINISHED_AUTHOR_WON
                n.subject = "Ouch! You lost %s's lottery \"%s\". You have 24h to complain." % (bet.author.username, bet.title)
        n.bet = bet
        return n

    @staticmethod
    def bet_complaining_finished(bet, recipient=None):
        n = Notification()
        n.notification_type = Notification.TYPE_BET_COMPLAINING_FINISHED_CONFLICT
        n.recipient = recipient
        if bet.author == recipient:
            n.subject = "Your bet \"%s\" was closed without complains." % bet.title
        else:
            n.subject = "%s's bet \"%s\" was closed without complains." % (bet.author.username, bet.title)
        n.bet = bet
        return n

    @staticmethod
    def bet_complaining_finished_conflict(bet, recipient=None):
        '''
        Assuming there's a complain
        '''
        n = Notification()
        n.notification_type = Notification.TYPE_BET_COMPLAINING_FINISHED_CONFLICT
        if bet.is_simple() or bet.is_auction():
            n.recipient = bet.author
            n.subject = "%s complained your resolution on \"%s\". Another user will arbitrate this conflict." % (bet.accepted_bid.author, bet.title)
        elif bet.is_lottery():
            n.recipient = recipient
            n.subject = "%s's lottery \"%s\" is under conflict and it will be arbitrated by another user." % (bet.author, bet.title)
        n.bet = bet
        return n


class Notification(models.Model):
    
    TYPE_NEW_FOLLOWER                           = 1
    TYPE_BET_RECEIVED                           = 2
    TYPE_BET_ACCEPTED                           = 3
    TYPE_BID_POSTED                             = 4
    TYPE_BID_ACCEPTED                           = 5
    TYPE_BET_BIDDING_FINISHED                   = 6
    TYPE_BET_EVENT_FINISHED                     = 7
    TYPE_BET_RESOLVING_FINISHED_AUTHOR_WON      = 8
    TYPE_BET_RESOLVING_FINISHED_AUTHOR_LOST     = 9
    TYPE_BET_RESOLVING_FINISHED_NULL            = 10
    TYPE_BET_COMPLAINING_FINISHED               = 11 # No complains
    TYPE_BET_COMPLAINING_FINISHED_CONFLICT      = 12 # Conflict!
    TYPE_BET_ARBITRATING_FINISHED_AUTHOR_WON    = 13
    TYPE_BET_ARBITRATING_FINISHED_AUTHOR_LOST   = 14
    TYPE_BET_ARBITRATING_FINISHED_NULL          = 15

    NOTIFICATION_TYPE_CHOICES = (
        (TYPE_NEW_FOLLOWER, "New follower"),
        (TYPE_BET_RECEIVED, "Bet received"),
        (TYPE_BET_ACCEPTED, "Bet accepted"),
        (TYPE_BID_POSTED, "Bid posted"),
        (TYPE_BID_ACCEPTED, "Bid accepted"),
        (TYPE_BET_BIDDING_FINISHED, "Biding finished"),
        (TYPE_BET_EVENT_FINISHED, "Event finished"),
        (TYPE_BET_RESOLVING_FINISHED_AUTHOR_WON, "Resolving finished (bet author lost)"),
        (TYPE_BET_RESOLVING_FINISHED_AUTHOR_LOST, "Resolving finished (bet author won)"),
        (TYPE_BET_RESOLVING_FINISHED_NULL, "Resolving finished (null)"),
        (TYPE_BET_COMPLAINING_FINISHED, "Complaining finished (no complains)"),
        (TYPE_BET_COMPLAINING_FINISHED_CONFLICT, "Complaining finished (conflict)"),
        (TYPE_BET_ARBITRATING_FINISHED_AUTHOR_WON, "Arbitrating finished (author won)"),
        (TYPE_BET_ARBITRATING_FINISHED_AUTHOR_LOST, "Arbitrating finished (author lost)"),
        (TYPE_BET_ARBITRATING_FINISHED_NULL, "Arbitrating finished (null)"),
        )
    date = models.DateTimeField(auto_now_add=True, blank=True, null=True, editable=False)
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='notifications', blank=True, null=True)
    subject = models.CharField(max_length=255, blank=True, null=True)
    facebook_uid = models.CharField(max_length=255, blank=True, null=True)
    notification_type = models.CharField(max_length=63, blank=True, null=True, choices=NOTIFICATION_TYPE_CHOICES)
    bet = models.ForeignKey(Bet, related_name='notifications', blank=True, null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='subject_notifications', blank=True, null=True)
    is_new = models.BooleanField(blank=True, default=True)
    readed = models.BooleanField(blank=True, default=False)

    def __unicode__(self):
        return "%s - %s [%s]" % (self.date, self.position, self.user)