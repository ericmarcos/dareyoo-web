from __future__ import absolute_import
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from celery import shared_task
from .models import *

@shared_task(name='save_widget_activation')
def save_widget_activation(**kwargs):
    WidgetActivation.objects.create(
        widget=Widget.objects.get(name=kwargs.get('widget_name')),
        bet=kwargs.get('bet_id'),
        level=kwargs.get('level'),
        from_ip=kwargs.get('from_ip'),
        from_host=kwargs.get('from_host'),
        participate_result=kwargs.get('result'),
        medium_shared=kwargs.get('medium'),
        banner_clicked=kwargs.get('banner')
    )