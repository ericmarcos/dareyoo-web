#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from django.contrib.auth import get_user_model
from django.db import models
from bets.models import *
from wabots.models import BaseBotInstance
from wabots.utils import BotMessage

class DareyooBot(BaseBotInstance):
    current_bet = models.ForeignKey(Bet, blank=True, null=True)

    def input(self, time, user, msg):
        client = self.getDefaultClient()
        resp = ""
        regs = {1: r"""^(?P<type>basica|básica|basic):?\s+
                              (?P<title>.+)\s+
                              (por|for)\s+(?P<amount>\d+)\s*(y|yoo|yoos)?\s*
                              (contra|against|vs|a|to)\s+(?P<against>\d+)\s*(y|yoo|yoos)?
                              .*$""",
                2: r"""^(?P<type>subhasta|auction):?\s+
                                (?P<title>.+)\s+
                                (por|for)\s+(?P<amount>\d+)\s*(y|yoo|yoos)?$""",
                3: r"""^(?P<type>porra|pool):?\s+
                                (?P<title>.+)\s+
                                (por|for)\s+(?P<amount>\d+)\s*(y|yoo|yoos)?$"""}
        for t, reg in regs.items():
            regex = re.compile(reg, re.IGNORECASE|re.UNICODE|re.VERBOSE)
            r = regex.search(msg)
            if r:
                if user and user.whatsapp_verified:
                    p = r.groupdict()
                    params = {'bet_type': t,
                              'title': p.get('title'),
                              'amount': int(p.get('amount')),
                              'bidding_deadline': timezone.now() + datetime.timedelta(minutes=20),
                              'event_deadline': timezone.now() + datetime.timedelta(minutes=60*24),
                              'public': int(p.get('amount'))}
                    if t == 1:
                        params['odds'] = float(params['amount'] + int(p.get('against'))) / params['amount']
                    b = BetFactory.create(**params)
                    b.set_author(user)
                    b.save()
                    self.current_bet = b
                    resp = "Apuesta creada!\n[%s]\"%s\"" % (b.id, b.title)
                else:
                    resp = "Tienes que verificar tu numero de whatsapp para poder crear apuestas"
        if resp:
            return BotMessage.textMsg(client, resp)
        return BotMessage.noopMsg()
