#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django import dispatch
from django.conf import settings
from celery.execute import send_task
from .models import *


message_received = dispatch.Signal(providing_args=["client", "conversation_jid", "user_jid", "msg"])

@dispatch.receiver(message_received, sender=Client)
def message_received_listener(sender, client, conversation_jid, user_jid, msg, **kwargs):
    if getattr(settings, "WA_RESPONSE_CELERY", True):
        send_task('process_message', [client.id, conversation_jid, user_jid, msg])
    else:
        process_message(client.id, conversation_jid, user_jid, msg)
