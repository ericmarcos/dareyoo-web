#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
import importlib, operator
from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from celery import shared_task, chain

@shared_task(name='process_message')
def task_process_message(client_id, conversation_jid, user_jid, msg):
    process_message(client_id, conversation_jid, user_jid, msg)


@shared_task(name='get_response')
def task_get_response(conversation_id, time, user_id, msg):
    c = Conversation.objects.get(id=conversation_id)
    if user_id:
        u = get_user_model().objects.get(id=user_id)
        c.get_response(time, u, msg)
    else:
        c.get_response(time, None, msg)


@shared_task(name='send_start_typing')
def task_send_start_typing(client_id, jid):
    ClientsManager.getClient(client_id).startTyping(jid)

@shared_task(name='send_stop_typing')
def task_send_stop_typing(client_id, jid):
    ClientsManager.getClient(client_id).stopTyping(jid)


@shared_task(name='send_message')
def task_send_message(conversation_id, client_id, msg, media=None):
    c = Conversation.objects.get(id=conversation_id)
    if media:
        c.sendImage(ClientsManager.getClient(client_id), media)
    else:
        c.send(ClientsManager.getClient(client_id), msg)

def get_chain_send_msg(conversation_id, client_id, msg, media=None, simulate_typing=True):
    c = Conversation.objects.get(id=conversation_id)
    if simulate_typing and not media:
        reaction_time = 1 #seconds
        typing_speed = 0.2 #chars per second
        typing_time = len(msg) * typing_speed
        return (task_send_start_typing.si(client_id, c.jid).set(countdown=reaction_time) |
              task_send_stop_typing.si(client_id, c.jid).set(countdown=typing_time) |
              task_send_message.si(conversation_id, client_id, msg, media=media).set(countdown=0.1))
    else:
        return task_send_message.si(conversation_id, client_id, msg, media=media).set(countdown=0.1)

def get_chain_send_many(conversation_id, bot_msgs, simulate_typing=True):
    tasks = [get_chain_send_msg(conversation_id,
                                m.client.id,
                                m.msg_body if not m.isMedia() else None,
                                m.msg_body if m.isMedia() else None,
                                simulate_typing).set(immutable=True)
            for m in bot_msgs]
    return reduce(operator.or_, tasks)

from .models import *