from datetime import datetime, timedelta
from celery import shared_task
from users.models import *
from django.conf import settings
from django.utils.timezone import now

from django.core.mail import EmailMultiAlternatives
from django.template import Context
from django.template.loader import render_to_string

@shared_task(name='free_coins')
def free_coins(**kwargs):
    '''Recurrent task that gives free free coins
    to all users under MAX_FREE_COINS'''
    users = DareyooUser.objects.filter(coins_available__lt=settings.MAX_FREE_COINS)
    #TODO: should it be coins_available or coins_available - coins_locked?
    for user in users:
        if user.coins_available < settings.MAX_FREE_COINS - settings.FREE_COINS_INTERVAL_AMOUNT:
            amount = settings.FREE_COINS_INTERVAL_AMOUNT
        elif user.coins_available < settings.MAX_FREE_COINS:
            amount = settings.MAX_FREE_COINS - user.coins_available
        user.coins_available += amount
        user.save()
        ur = UserRefill()
        ur.user = user
        ur.amount = amount
        ur.refill_type = 'free'
        ur.save()

@shared_task(name='send_email')
def send_email(**kwargs):
    from_addr = kwargs.get('from_addr', settings.DEFAULT_FROM_ADDR)
    to_addr = kwargs.get('to_addr')
    subject = kwargs.get('subject', '')
    text_body = kwargs.get('text_body', '')
    html_body = kwargs.get('html_body', '')

    template_data = kwargs.get('template_data', {})
    plaintext_context = Context(autoescape=False)  # HTML escaping not appropriate in plaintext

    subject_template = kwargs.get('subject_template')
    if subject_template:
        subject = render_to_string(subject_template, template_data, plaintext_context)

    text_body_template = kwargs.get('text_body_template')
    if text_body_template:
        text_body = render_to_string(text_body_template, template_data, plaintext_context)

    html_body_template = kwargs.get('html_body_template')
    if html_body_template:
        html_body = render_to_string(html_body_template, template_data)

    msg = EmailMultiAlternatives(subject=subject, from_email=from_addr,
                                to=[to_addr], body=text_body)
    msg.attach_alternative(html_body, "text/html")
    msg.send()
