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
        bet_id=kwargs.get('bet_id'),
        level=kwargs.get('level'),
        from_ip=kwargs.get('from_ip'),
        from_host=kwargs.get('from_host'),
        participate_result=kwargs.get('participate_result'),
        medium_shared=kwargs.get('medium_shared'),
        banner_clicked=kwargs.get('banner_clicked')
    )