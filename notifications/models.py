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
        n.subject = u"%s ha empezado a seguirte!" % follower.username
        n.user = follower
        return n

    @staticmethod
    def bet_received(recipient, bet):
        n = Notification()
        n.recipient = recipient
        n.notification_type = Notification.TYPE_BET_RECEIVED
        n.subject = u"%s te ha enviado una apuesta: \"%s\"" % (bet.author.username, bet.title)
        n.bet = bet
        return n

    @staticmethod
    def bet_accepted(bet):
        n = Notification()
        n.recipient = bet.author
        n.notification_type = Notification.TYPE_BET_ACCEPTED
        n.subject = u"%s ha aceptado tu apuesta \"%s\"" % (bet.accepted_bid.author.username, bet.title)
        n.bet = bet
        n.user = bet.accepted_bid.author
        return n

    @staticmethod
    def bid_posted(bid):
        n = Notification()
        n.recipient = bid.bet.author
        n.notification_type = Notification.TYPE_BID_POSTED
        if bid.bet.is_auction():
            n.subject = u"%s ha añadido una oferta a tu subasta: \"%s\"" % (bid.author.username, bid.title)
        elif bid.bet.is_lottery():
            n.subject = u"%s ha añadido un resultado a tu porra: \"%s\"" % (bid.author.username, bid.title)
        n.bet = bid.bet
        n.bid = bid
        n.user = bid.author
        return n

    @staticmethod
    def bid_deleted(bid):
        n = Notification()
        n.recipient = bid.author
        n.notification_type = Notification.TYPE_BID_DELETED
        if bid.bet.is_auction():
            n.subject = u"%s ha borrado tu oferta \"%s\"" % (bid.bet.author.username, bid.title)
        elif bid.bet.is_lottery():
            n.subject = u"%s ha borrado tu resultado \"%s\"" % (bid.bet.author.username, bid.title)
        n.bet = bid.bet
        n.user = bid.bet.author
        return n

    @staticmethod
    def bid_accepted(bid):
        n = Notification()
        n.recipient = bid.author
        n.notification_type = Notification.TYPE_BID_ACCEPTED
        n.subject = u"%s ha aceptado tu oferta \"%s\" en la apuesta \"%s\"" % (bid.bet.author.username, bid.title, bid.bet.title)
        n.bet = bid.bet
        return n

    @staticmethod
    def bet_event_finished(bet):
        n = Notification()
        n.recipient = bet.author
        n.notification_type = Notification.TYPE_BET_EVENT_FINISHED
        n.subject = u"Tu apuesta \"%s\" ha finalizado! Tienes 24h para resolverla." % bet.title
        n.bet = bet
        return n

    @staticmethod
    def bet_resolving_finished(bet, recipient=None):
        n = Notification()
        if bet.is_simple() or bet.is_auction():
            n.recipient = bet.accepted_bid.author
            if bet.claim == Bet.CLAIM_WON:
                n.notification_type = Notification.TYPE_BET_RESOLVING_FINISHED_AUTHOR_WON
                n.subject = u"Que lástima... has perdido la apuesta \"%s\"." % bet.title
            elif bet.claim == Bet.CLAIM_LOST:
                n.notification_type = Notification.TYPE_BET_RESOLVING_FINISHED_AUTHOR_LOST
                n.subject = u"¡Felicidades! Eres el ganador de la apuesta \"%s\"." % bet.title
            elif bet.claim == Bet.CLAIM_NULL:
                n.notification_type = Notification.TYPE_BET_RESOLVING_FINISHED_NULL
                n.subject = u"Que lástima... has perdido la apuesta \"%s\"." % bet.title
            #if bet.claim_message:
            #    n.subject = bet.claim_message
        elif bet.is_lottery():
            n.recipient = recipient
            if bet.claim == Bet.CLAIM_NULL:
                n.notification_type = Notification.TYPE_BET_RESOLVING_FINISHED_NULL
                n.subject = u"Que lástima... has perdido la porra \"%s\"." % bet.title
            elif recipient in bet.claim_lottery_winner.participants.all():
                n.notification_type = Notification.TYPE_BET_RESOLVING_FINISHED_AUTHOR_LOST
                n.subject = u"¡Felicidades! Eres el ganador de la porra \"%s\"." % bet.title
            else:
                n.notification_type = Notification.TYPE_BET_RESOLVING_FINISHED_AUTHOR_WON
                n.subject = u"Que lástima... has perdido la porra \"%s\"." % bet.title
        n.bet = bet
        return n

    @staticmethod
    def bet_complaining_finished(bet, recipient=None):
        '''
        n = Notification()
        n.notification_type = Notification.TYPE_BET_COMPLAINING_FINISHED
        n.recipient = recipient
        if bet.author == recipient:
            n.subject = "Tu apuesta \"%s\" ha finalizado sin reclamaciones." % bet.title
        else:
            n.subject = "La apuesta de %s \"%s\" ha finalizado sin reclamaciones." % (bet.author.username, bet.title)
        n.bet = bet
        return n
        '''
        pass

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
        n.recipient = recipient
        if bet.is_simple() or bet.is_auction():
            if recipient == bet.author:
                winners = bet.winners()
                winner = winners[0] if winners else None
                if winner == recipient:
                    n.notification_type = Notification.TYPE_BET_ARBITRATING_FINISHED_AUTHOR_WON
                    n.subject = u"%s ha arbitrado tu apuesta \"%s\" y ha decidido que has ganado." % (bet.referee.username, bet.title)
                elif winner == None:
                    n.notification_type = Notification.TYPE_BET_ARBITRATING_FINISHED_AUTHOR_LOST
                    n.subject = u"%s ha arbitrado tu apuesta \"%s\" y ha decidido que la apuesta es nula." % (bet.referee.username, bet.title)
                else:
                    n.notification_type = Notification.TYPE_BET_ARBITRATING_FINISHED_AUTHOR_LOST
                    n.subject = u"%s ha arbitrado tu apuesta \"%s\" y ha decidido que has perdido." % (bet.referee.username, bet.title)
            elif recipient == bet.accepted_bid.author:
                winners = bet.winners()
                winner = winners[0] if winners else None
                if winner == recipient:
                    n.notification_type = Notification.TYPE_BET_ARBITRATING_FINISHED_AUTHOR_WON
                    n.subject = u"%s ha arbitrado la apuesta de %s \"%s\" y ha decidido que has ganado." % (bet.referee.username, bet.author.username, bet.title)
                elif winner == None:
                    n.notification_type = Notification.TYPE_BET_ARBITRATING_FINISHED_AUTHOR_LOST
                    n.subject = u"%s ha arbitrado la apuesta de %s \"%s\" y ha decidido que la apuesta es nula." % (bet.referee.username, bet.author.username, bet.title)
                else:
                    n.notification_type = Notification.TYPE_BET_ARBITRATING_FINISHED_AUTHOR_LOST
                    n.subject = u"%s ha arbitrado la apuesta de %s \"%s\" y ha decidido que has perdido." % (bet.referee.username, bet.author.username, bet.title)
        elif bet.is_lottery():
            winners = bet.winners() or []
            if recipient in winners:
                n.notification_type = Notification.TYPE_BET_ARBITRATING_FINISHED_AUTHOR_WON
                n.subject = u"%s ha arbitrado la porra \"%s\" y ha decidido que has ganado." % (bet.referee.username, bet.title)
            else:
                n.notification_type = Notification.TYPE_BET_ARBITRATING_FINISHED_AUTHOR_LOST
                n.subject = u"%s ha arbitrado la porra \"%s\" y ha decidido que has perdido." % (bet.referee.username, bet.title)
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

    TEMPLATE_NAMES = {
        1: "Nuevo seguidor",
        2: "Invite Email (white)",
        3: "Basica aceptada",
        4: {"auction": "Nueva oferta", "lottery":"Nuevo resultado"},
        44: {"auction": "Oferta eliminada", "lottery":"Resultado eliminado"},
        5: "Oferta aceptada",
        6: "X",
        7: {"simple":"Resolver (basica)", "auction": "Resolver (subasta)", "lottery":"Resolver (porra)"},
        8: {"simple":"Basica perdida", "auction": "Subasta perdida", "lottery":"Porra perdida"},
        9: {"simple":"Apuesta ganada (basica)", "auction": "Apuesta ganada (subasta)", "lottery":"Apuesta ganada (porra)"},
        10: {"simple":"Basica perdida", "auction": "Subasta perdida", "lottery":"Porra perdida"},
        11: "X",
        12: {"simple":"Apuesta reclamada (basica)", "auction": "Apuesta reclamada (subasta)", "lottery":"Apuesta reclamada (porra)"}, #add (author) to lottery
        13: {"simple":"Apuesta arbitrada (basica)", "auction": "Apuesta arbitrada (subasta)", "lottery":"Apuesta arbitrada (porra)"},
        14: {"simple":"Apuesta arbitrada (basica)", "auction": "Apuesta arbitrada (subasta)", "lottery":"Apuesta arbitrada (porra)"},
        15: "X",
    }

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

    '''
    def send_notification_email(self):
        if self.recipient.email and self.recipient.email_notifications:
            if self.bet:
                link = 'http://www.dareyoo.com/app/main/bet/%s' % self.bet.id
                link_text = 'www.dareyoo.com/app/main/bet/%s' % self.bet.id
            elif self.user:
                link = 'http://www.dareyoo.com/app/profile/%s/bets' % self.user.id
                link_text = 'www.dareyoo.com/app/profile/%s/bets' % self.user.id
            if self. notification_type == Notification.TYPE_BET_RECEIVED:
                link = str(link) + "?utm_source=invite_email&utm_medium=email&utm_campaign=initial"
            kwargs = {
                'from_addr': settings.DEFAULT_FROM_EMAIL,
                'to_addr': self.recipient.email,
                'subject_template': "email/notification/subject.txt",
                'text_body_template': "email/notification/body.txt",
                'html_body_template': "email/notification/body.html",
                'template_data': {
                    'username': self.recipient.username,
                    'subject': self.subject,
                    'link': link,
                    'link_text': link_text
                }
            }
            
            send_task('send_email', kwargs=kwargs)
    '''
    def send_notification_email(self):
        if self.recipient.email and self.recipient.email_notifications:
            kwargs = {
                'to_addr': self.recipient.email,
                'subject_template': "email/notification/subject.txt",
                'template_data': {
                    'subject': self.subject
                }
            }

            t = int(self.notification_type)
            
            if t == Notification.TYPE_NEW_FOLLOWER:
                kwargs['template_name'] = Notification.TEMPLATE_NAMES[t]
                kwargs['template_data']['FNAME'] = self.recipient.username
                kwargs['template_data']['FOLLOWER_URL'] = self.get_user_url()
                kwargs['template_data']['FOLLOWER_PIC'] = self.user.get_profile_pic_url()
                kwargs['template_data']['FOLLOWER'] = self.user.username
                kwargs['template_data']['FOLLOWER_DESC'] = self.user.description or ""
            
            if t == Notification.TYPE_BET_RECEIVED:
                kwargs['template_name'] = Notification.TEMPLATE_NAMES[t]
                kwargs['template_data']['FNAME'] = self.bet.author.username
                kwargs['template_data']['AUTHOR_URL'] = self.get_user_url(self.bet.author)
                kwargs['template_data']['AUTHOR_PIC'] = self.bet.author.get_profile_pic_url()
                kwargs['template_data']['BETTITLE'] = self.bet.title
                kwargs['template_data']['BET_URL'] = self.get_bet_url()
            
            if t == Notification.TYPE_BET_ACCEPTED:
                kwargs['template_name'] = Notification.TEMPLATE_NAMES[t]
                kwargs['template_data']['FNAME'] = self.user.username
                kwargs['template_data']['BETTITLE'] = self.bet.title
                kwargs['template_data']['BET_URL'] = self.get_bet_url()
            
            if t == Notification.TYPE_BID_POSTED:
                kwargs['template_name'] = Notification.TEMPLATE_NAMES[t][self.bet.get_type_name()]
                kwargs['template_data']['BETTITLE'] = self.bet.title
                kwargs['template_data']['BIDAUTHOR'] = self.bid.author.username
                kwargs['template_data']['RESULT'] = self.bid.title
                kwargs['template_data']['AMOUNT'] = self.bid.amount
                kwargs['template_data']['YOOS'] = self.bet.amount + self.bid.amount
                kwargs['template_data']['BET_URL'] = self.get_bet_url()
            
            if t == Notification.TYPE_BID_DELETED:
                kwargs['template_name'] = Notification.TEMPLATE_NAMES[t][self.bet.get_type_name()]
                kwargs['template_data']['FNAME'] = self.bet.author.username
                kwargs['template_data']['BETTITLE'] = self.bet.title
                kwargs['template_data']['BET_URL'] = self.get_bet_url()
            
            if t == Notification.TYPE_BID_ACCEPTED:
                kwargs['template_name'] = Notification.TEMPLATE_NAMES[t]
                kwargs['template_data']['FNAME'] = self.bet.author.username
                kwargs['template_data']['BETTITLE'] = self.bet.title
                kwargs['template_data']['BET_URL'] = self.get_bet_url()
            
            if t == Notification.TYPE_BET_EVENT_FINISHED:
                kwargs['template_name'] = Notification.TEMPLATE_NAMES[t][self.bet.get_type_name()]
                kwargs['template_data']['FNAME'] = self.recipient.username
                kwargs['template_data']['BETTITLE'] = self.bet.title
                kwargs['template_data']['BET_URL'] = self.get_bet_url()
            
            if t == Notification.TYPE_BET_RESOLVING_FINISHED_AUTHOR_WON:
                kwargs['template_name'] = Notification.TEMPLATE_NAMES[t][self.bet.get_type_name()]
                kwargs['template_data']['BETTITLE'] = self.bet.title
                if self.recipient == self.bet.author and not self.bet.is_lottery():
                    kwargs['template_data']['BIDAUTHOR'] = self.bet.accepted_bid.author.username
                    kwargs['template_data']['BID'] = self.bet.accepted_bid.title
                #kwargs['template_data']['POINTS'] = self.bet.points.filter(user=self.recipient).first().points
                kwargs['template_data']['BET_URL'] = self.get_bet_url()
            
            if t == Notification.TYPE_BET_RESOLVING_FINISHED_AUTHOR_LOST:
                kwargs['template_name'] = Notification.TEMPLATE_NAMES[t][self.bet.get_type_name()]
                if not self.bet.is_lottery():
                    kwargs['template_data']['BIDAUTHOR'] = self.bet.accepted_bid.author.username
                    kwargs['template_data']['BID'] = self.bet.accepted_bid.title
                    if self.recipient == self.bet.author:
                        kwargs['template_name'] += " (autor)"
                kwargs['template_data']['AUTHORNAME'] = self.bet.author.username
                kwargs['template_data']['BETTITLE'] = self.bet.title
                #kwargs['template_data']['POINTS'] = self.bet.points.filter(user=self.recipient).first().points
                kwargs['template_data']['BET_URL'] = self.get_bet_url()
            
            if t == Notification.TYPE_BET_RESOLVING_FINISHED_NULL:
                kwargs['template_name'] = Notification.TEMPLATE_NAMES[t][self.bet.get_type_name()]
                kwargs['template_data']['BETTITLE'] = self.bet.title
                #kwargs['template_data']['POINTS'] = self.bet.points.filter(user=self.recipient).first().points
                kwargs['template_data']['BET_URL'] = self.get_bet_url()
            
            if t == Notification.TYPE_BET_COMPLAINING_FINISHED_CONFLICT:
                kwargs['template_name'] = Notification.TEMPLATE_NAMES[t][self.bet.get_type_name()]
                if self.bet.is_lottery():
                    kwargs['template_data']['BETAUTHOR'] = self.bet.author.username
                    kwargs['template_data']['FNAME'] = self.bet.bids.filter(claim_author__isnull=False).first().claim_author.username
                    if self.recipient == self.bet.author:
                        kwargs['template_name'] += " (autor)"
                else:
                    kwargs['template_data']['FNAME'] = self.bet.accepted_bid.author.username
                kwargs['template_data']['BETTITLE'] = self.bet.title
                kwargs['template_data']['BET_URL'] = self.get_bet_url()
            
            if t == Notification.TYPE_BET_ARBITRATING_FINISHED_AUTHOR_WON or t == Notification.TYPE_BET_ARBITRATING_FINISHED_AUTHOR_LOST:
                kwargs['template_name'] = Notification.TEMPLATE_NAMES[t][self.bet.get_type_name()]
                if self.bet.is_lottery():
                    kwargs['template_data']['RESULT'] = self.bet.referee_lottery_winner.title
                else:
                    w = self.bet.winners()
                    kwargs['template_data']['WINNER'] = w[0].username if w else "Nadie, la apuesta es nula."
                kwargs['template_data']['REFEREE'] = self.bet.referee.username
                kwargs['template_data']['BETTITLE'] = self.bet.title
                kwargs['template_data']['BET_URL'] = self.get_bet_url()

            send_task('send_template_email', kwargs=kwargs)

    def get_user_url(self, user=None):
        if user:
            return 'http://www.dareyoo.com/app/profile/%s/bets' % user.id
        if self.user:
            return 'http://www.dareyoo.com/app/profile/%s/bets' % self.user.id
        return 'http://www.dareyoo.com'

    def get_bet_url(self):
        if self.bet:
            return 'http://www.dareyoo.com/app/main/bet/%s' % self.bet.id
        return 'http://www.dareyoo.com'

    def __unicode__(self):
        return "%s - %s [%s]" % (self.date, self.recipient, self.subject)


import notifications.signals