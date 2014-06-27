#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.db import models
from django.conf import settings
from celery.execute import send_task
from bets.models import Bet
from .models import *


class NotificationFactory:

    @staticmethod
    def new_follower(recipient, follower):
        n = Notification()
        n.recipient = recipient
        n.notification_type = Notification.TYPE_NEW_FOLLOWER
        n.subject = "%s ha empezado a seguirte!" % follower.username
        n.user = follower
        return n

    @staticmethod
    def bet_received(recipient, bet):
        n = Notification()
        n.recipient = recipient
        n.notification_type = Notification.TYPE_BET_RECEIVED
        n.subject = "%s te ha enviado una apuesta: \"%s\"" % (bet.author.username, bet.title)
        n.bet = bet
        return n

    @staticmethod
    def bet_accepted(bet):
        n = Notification()
        n.recipient = bet.author
        n.notification_type = Notification.TYPE_BET_ACCEPTED
        n.subject = "%s ha aceptado tu apuesta \"%s\"" % (bet.accepted_bid.author.username, bet.title)
        n.bet = bet
        n.user = bet.accepted_bid.author
        return n

    @staticmethod
    def bid_posted(bid):
        n = Notification()
        n.recipient = bid.bet.author
        n.notification_type = Notification.TYPE_BID_POSTED
        if bid.bet.is_auction():
            n.subject = u"%s ha añadido una oferta: \"%s\"" % (bid.author.username, bid.title)
        elif bid.bet.is_lottery():
            n.subject = u"%s ha añadido un resultado: \"%s\"" % (bid.author.username, bid.title)
        n.bet = bid.bet
        n.user = bid.author
        return n

    @staticmethod
    def bid_deleted(bid):
        n = Notification()
        n.recipient = bid.author
        n.notification_type = Notification.TYPE_BID_DELETED
        if bid.bet.is_auction():
            n.subject = "%s ha borrado tu oferta \"%s\"" % (bid.bet.author.username, bid.title)
        elif bid.bet.is_lottery():
            n.subject = "%s ha borrado tu resultado \"%s\"" % (bid.bet.author.username, bid.title)
        n.bet = bid.bet
        n.user = bid.bet.author
        return n

    @staticmethod
    def bid_accepted(bid):
        n = Notification()
        n.recipient = bid.author
        n.notification_type = Notification.TYPE_BID_ACCEPTED
        n.subject = "%s ha aceptado tu oferta \"%s\" en la apuesta \"%s\"" % (bid.bet.author.username, bid.title, bid.bet.title)
        n.bet = bid.bet
        return n

    @staticmethod
    def bet_event_finished(bet):
        n = Notification()
        n.recipient = bet.author
        n.notification_type = Notification.TYPE_BET_EVENT_FINISHED
        n.subject = "Tu apuesta \"%s\" ha finalizado! Tienes 24h para resolverla." % bet.title
        n.bet = bet
        return n

    @staticmethod
    def bet_resolving_finished(bet, recipient=None):
        n = Notification()
        if bet.is_simple() or bet.is_auction():
            n.recipient = bet.accepted_bid.author
            if bet.claim == Bet.CLAIM_WON:
                n.notification_type = Notification.TYPE_BET_RESOLVING_FINISHED_AUTHOR_WON
                n.subject = "%s ha declarado que ha perdido su apuesta \"%s\". Tienes 24h para reclamar." % (bet.author.username, bet.title)
            elif bet.claim == Bet.CLAIM_LOST:
                n.notification_type = Notification.TYPE_BET_RESOLVING_FINISHED_AUTHOR_LOST
                n.subject = "%s ha declarado que ha ganado su apuesta \"%s\". Tienes 24h para reclamar." % (bet.author.username, bet.title)
            elif bet.claim == Bet.CLAIM_NULL:
                n.notification_type = Notification.TYPE_BET_RESOLVING_FINISHED_NULL
                n.subject = "%s ha declarado que nadie ha ganado su apuesta \"%s\". Tienes 24h para reclamar." % (bet.author.username, bet.title)
            #if bet.claim_message:
            #    n.subject = bet.claim_message
        elif bet.is_lottery():
            n.recipient = recipient
            if bet.claim == Bet.CLAIM_NULL:
                n.notification_type = Notification.TYPE_BET_RESOLVING_FINISHED_NULL
                n.subject = "%s ha declarado que nadie ha ganado su porra \"%s\". Tienes 24h para reclamar." % (bet.author.username, bet.title)
            elif recipient in bet.claim_lottery_winner.participants.all():
                n.notification_type = Notification.TYPE_BET_RESOLVING_FINISHED_AUTHOR_LOST
                n.subject = "%s ha declarado que has ganado la porra \"%s\"." % (bet.author.username, bet.title)
            else:
                n.notification_type = Notification.TYPE_BET_RESOLVING_FINISHED_AUTHOR_WON
                n.subject = "%s ha declarado que has perdido la porra \"%s\". Tienes 24h para reclamar." % (bet.author.username, bet.title)
        n.bet = bet
        return n

    @staticmethod
    def bet_complaining_finished(bet, recipient=None):
        n = Notification()
        n.notification_type = Notification.TYPE_BET_COMPLAINING_FINISHED
        n.recipient = recipient
        if bet.author == recipient:
            n.subject = "Tu apuesta \"%s\" ha finalizado sin reclamaciones." % bet.title
        else:
            n.subject = "La apuesta de %s \"%s\" ha finalizado sin reclamaciones." % (bet.author.username, bet.title)
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
            n.subject = u"%s ha reclamado tu resolución en la apuesta \"%s\". Otro usuario arbitrará este conflicto." % (bet.accepted_bid.author.username, bet.title)
        elif bet.is_lottery():
            n.recipient = recipient
            if bet.author == recipient:
                n.subject = u"Tu resolución en la porra \"%s\" ha sido reclamada y será arbitrada por otro usuario" % bet.title
            else:
                n.subject = u"La porra de %s \"%s\" está bajo conflicto y será arbitrada por otro usuario." % (bet.author.username, bet.title)
        n.bet = bet
        return n

    @staticmethod
    def bet_arbitrated(bet, recipient=None):
        '''
        Assuming there's a referee
        '''
        n = Notification()
        n.notification_type = Notification.TYPE_BET_COMPLAINING_FINISHED_CONFLICT
        n.recipient = recipient
        if bet.is_simple() or bet.is_auction():
            if recipient == bet.author:
                winner = dict(enumerate(bet.winners())).get(0)
                if winner == recipient:
                    n.subject = "%s ha arbitrado tu apuesta \"%s\" y ha decidido que has ganado." % (bet.referee.username, bet.title)
                elif winner == None:
                    n.subject = "%s ha arbitrado tu apuesta \"%s\" y ha decidido que la apuesta es nula." % (bet.referee.username, bet.title)
                else:
                    n.subject = "%s ha arbitrado tu apuesta \"%s\" y ha decidido que has perdido." % (bet.referee.username, bet.title)
            elif recipient == bet.accepted_bid.author:
                winner = dict(enumerate(bet.winners())).get(0)
                if winner == recipient:
                    n.subject = "%s ha arbitrado la apuesta de %s \"%s\" y ha decidido que has ganado." % (bet.referee.username, bet.author.username, bet.title)
                elif winner == None:
                    n.subject = "%s ha arbitrado la apuesta de %s \"%s\" y ha decidido que la apuesta es nula." % (bet.referee.username, bet.author.username, bet.title)
                else:
                    n.subject = "%s ha arbitrado la apuesta de %s \"%s\" y ha decidido que has perdido." % (bet.referee.username, bet.author.username, bet.title)
        elif bet.is_lottery():
            if recipient in bet.winners():
                n.subject = "%s ha arbitrado la porra \"%s\" y ha decidido que has ganado." % (bet.referee.username, bet.title)
            else:
                n.subject = "%s ha arbitrado la porra \"%s\" y ha decidido que has perdido." % (bet.referee.username, bet.title)
        n.bet = bet
        return n


class Notification(models.Model):
    
    TYPE_NEW_FOLLOWER                           = 1
    TYPE_BET_RECEIVED                           = 2
    TYPE_BET_ACCEPTED                           = 3
    TYPE_BID_POSTED                             = 4
    TYPE_BID_DELETED                            = 44
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

    def send_notification_email(self):
        if self.recipient.email and self.recipient.email_notifications:
            if self.bet:
                link = 'http://www.dareyoo.com/app/main/bet/%s' % self.bet.id
            elif self.user:
                link = 'http://www.dareyoo.com/app/profile/%s/bets' % self.user.id
            kwargs = {
                'from_addr': "no-reply@dareyoo.com",
                'to_addr': self.recipient.email,
                'subject_template': "email/notification/subject.txt",
                'text_body_template': "email/notification/body.txt",
                'html_body_template': "email/notification/body.html",
                'template_data': {
                    'username': self.recipient.username,
                    'subject': self.subject,
                    'link': link
                }
            }
            
            send_task('send_email', kwargs=kwargs)

    def __unicode__(self):
        return "%s - %s [%s]" % (self.date, self.recipient, self.subject)


import notifications.signals