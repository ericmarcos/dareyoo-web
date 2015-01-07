from datetime import datetime, timedelta
from celery import shared_task
from users.models import *
from django.conf import settings
from django.utils.timezone import now

from django.core.mail import EmailMultiAlternatives, EmailMessage
from django.template import Context
from django.template.loader import render_to_string

import mailchimp

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
    msg.send(fail_silently=True)


@shared_task(name='send_template_email')
def send_template_email(**kwargs):
    from_addr = kwargs.get('from_addr', settings.DEFAULT_FROM_ADDR)
    to_addr = kwargs.get('to_addr')
    subject = kwargs.get('subject', '')
    text_body = kwargs.get('text_body', '')
    html_body = kwargs.get('html_body', '')
    template_name = kwargs.get('template_name', '')
    template_data = kwargs.get('template_data', {})
    plaintext_context = Context(autoescape=False)  # HTML escaping not appropriate in plaintext

    subject_template = kwargs.get('subject_template')
    if subject_template:
        subject = render_to_string(subject_template, template_data, plaintext_context)

    msg = EmailMessage(subject=subject, from_email=from_addr,
                   to=[to_addr,])
    msg.template_name = template_name
    msg.global_merge_vars = template_data
    msg.send(fail_silently=True)


@shared_task(name='register_email_mailchimp')
def register_email_mailchimp(**kwargs):
    user_id = kwargs.get('user_id')
    user = DareyooUser.objects.get(id=user_id)
    if user and user.email:
        try:
            conn = mailchimp.utils.get_connection()
            dy_main_list = conn.get_list_by_id(settings.MAILCHIMP_LISTS.get('Dareyoo'))
            dy_main_list.subscribe(user.email, {'EMAIL': user.email, 'FNAME': user.username}, double_optin=False)
            dy_news_list = conn.get_list_by_id(settings.MAILCHIMP_LISTS.get('Dareyoo News'))
            dy_news_list.subscribe(user.email, {'EMAIL': user.email, 'FNAME': user.username}, double_optin=False)
        except:
            pass