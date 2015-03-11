import re
import random
import pytz
from dateutil import rrule
from django.core.urlresolvers import reverse
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.conf import settings
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from django.utils import timezone
from django.http import *
from django.shortcuts import render_to_response,redirect, get_object_or_404
from django.template import RequestContext
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.cache import cache
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from celery.execute import send_task
from ipware.ip import get_ip
from users.models import *
from bets.models import Bet
from .serializers import *
from .models import *


@api_view(['POST',])
@permission_classes([])
def widget_activation(request, widget, level, format=None):
    levels = {"impression": 1, "interaction": 2, "participate":3, "register": 4, "login": 5, "share": 6, "banner": 7}
    if level not in levels.keys():
        return Response({'detail': "Invalid activation level"}, status=status.HTTP_400_BAD_REQUEST)
    try:
        widget_activation_params = {
            'widget_name': widget,
            'bet_id': request.DATA.get('bet_id'),
            'level': levels[level],
            'from_ip': get_ip(request),
            'from_host': request.META.get('HTTP_HOST'),
            'participate_result': request.DATA.get('result'),
            'medium_shared': request.DATA.get('medium'),
            'banner_clicked': request.DATA.get('banner')
        }

        if level == "impression":
            participated_bets = request.DATA.get('participated_bets', [])
            widget_json = cache.get("widget_" + widget)
            if not widget_json:
                w = Widget.objects.get(name=widget)
                serializer = WidgetSerializer(w, context={'request': request})
                widget_json = serializer.data
                cache.set("widget_" + widget, widget_json, 30)
            available_bets = [b.get('id') for b in widget_json.get('bets') if b.get('id') not in participated_bets]
            first_bet_id = None
            if available_bets:
                first_bet_id = random.choice(available_bets)
                widget_activation_params['bet_id'] = first_bet_id
            widget_json.update({'first_bet_id': first_bet_id})
            send_task('save_widget_activation', kwargs=widget_activation_params)
            return Response(widget_json)
        send_task('save_widget_activation', kwargs=widget_activation_params)
    except Exception, e:
        return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    return Response({'status': 'created'})


@user_passes_test(lambda u: u.is_staff)
def new_users(request):
    today_users = DareyooUser.objects.real().joined_day()
    week_users = DareyooUser.objects.real().joined_week()
    return render_to_response('new_users.html', context_instance=RequestContext(request,
        {'today_users': today_users, 'week_users': week_users}))


@user_passes_test(lambda u: u.is_staff)
def inactive_users(request):
    one_day_wonders = DareyooUser.objects.real().one_day_wonders()
    inactive_month = DareyooUser.objects.real().churn_month()
    inactive_week = DareyooUser.objects.real().churn_week()
    return render_to_response('inactive_users.html', context_instance=RequestContext(request,
        {'one_day_wonders': one_day_wonders, 'inactive_month': inactive_month, 'inactive_week': inactive_week}))


@user_passes_test(lambda u: u.is_staff)
def main(request):
    if request.GET.get('range') and request.GET.get('range') in ['day', 'week', 'month']:
        request.session['range'] = request.GET.get('range')
        request.session['prev'] = 0
    elif not request.session.get('range'):
        request.session['range'] = 'day'
    if request.GET.get('prev') and int(request.GET.get('prev')) >= 0:
        request.session['prev'] = request.GET.get('prev')
    elif not request.session.get('prev'):
        request.session['prev'] = 0
    if request.GET.get('activation') and request.GET.get('activation') in ['login', 'participate', 'create']:
        request.session['activation'] = request.GET.get('activation')
    else:
        request.session['activation'] = 'login'
    n = DareyooUser.objects.n()
    fake = DareyooUser.objects.all().staff().count()
    leads = DareyooUser.objects.all().registered(False).count()
    rang = request.session.get('range')
    prev = int(request.session.get('prev'))
    total_bets = Bet.objects.all().count()
    total_basic = Bet.objects.all().simple().count()
    total_auction = Bet.objects.all().auction().count()
    total_lottery = Bet.objects.all().lottery().count()
    percent_basic = int(round(float(total_basic) / total_bets * 100)) if total_bets > 0 else 0
    percent_auction = int(round(float(total_auction) / total_bets * 100)) if total_bets > 0 else 0
    percent_lottery = int(round(float(total_lottery) / total_bets * 100)) if total_bets > 0 else 0
    total_closed_bets = Bet.objects.all().closed().count()
    percent_closed_bets = int(round(float(total_closed_bets) / total_bets * 100)) if total_bets > 0 else 0
    total_coins_available = int(DareyooUser.objects.total_coins_available())
    total_coins_locked = int(DareyooUser.objects.total_coins_locked())
    total_coins = total_coins_available + total_coins_locked
    percent_coins_available = int(round(float(total_coins_available) / total_coins * 100)) if total_coins > 0 else 0
    percent_coins_locked = int(round(float(total_coins_locked) / total_coins * 100)) if total_coins > 0 else 0
    coins_per_user = int(round(float(DareyooUser.objects.real().sum_coins()) / n)) if n > 0 else 0
    max_coins_per_user = int(DareyooUser.objects.real().order_by('-coins_available')[0].coins_available)
    if rang == 'day':
        begin_date = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=-prev)
        end_date = timezone.now() if int(prev) == 0 else begin_date + timedelta(days=1)
        new_real_users = DareyooUser.objects.real().joined_day(prev).count()
        n_users_before = DareyooUser.objects.real().joined_before_day(prev).count()
        new_leads = DareyooUser.objects.all().registered(False).joined_day(prev).count()
        active = DareyooUser.objects.real().active_day().count()
        churn_n = '--'
        churn = '--'
        new_bets = Bet.objects.all().created_day(prev).count()
        new_basic = Bet.objects.all().created_day(prev).simple().count()
        new_auction = Bet.objects.all().created_day(prev).auction().count()
        new_lottery = Bet.objects.all().created_day(prev).lottery().count()
        new_closed_bets = Bet.objects.all().finished_day(prev).count()
        new_free_coins = int(UserRefill.objects.all().created_day(prev).free().sum())
        new_paying_coins = int(UserRefill.objects.all().created_day(prev).paying().sum())
    elif rang == 'week':
        today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        begin_date = today + timedelta(days=-today.weekday() - 7*prev)
        end_date = timezone.now() if int(prev) == 0 else begin_date + timedelta(weeks=1)
        new_real_users = DareyooUser.objects.real().joined_week(prev).count()
        n_users_before = DareyooUser.objects.real().joined_before_week(prev).count()
        new_leads = DareyooUser.objects.all().registered(False).joined_week(prev).count()
        active = DareyooUser.objects.real().active_week().count()
        churn_n = DareyooUser.objects.real().churn_week().count()
        churn = int(round(float(churn_n) / n * 100)) if n > 0 else 0
        new_bets = Bet.objects.all().created_week(prev).count()
        new_basic = Bet.objects.all().created_week(prev).simple().count()
        new_auction = Bet.objects.all().created_week(prev).auction().count()
        new_lottery = Bet.objects.all().created_week(prev).lottery().count()
        new_closed_bets = Bet.objects.all().finished_week(prev).count()
        new_free_coins = int(UserRefill.objects.all().created_week(prev).free().sum())
        new_paying_coins = int(UserRefill.objects.all().created_week(prev).paying().sum())
    elif rang == 'month':
        begin_date = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0) + relativedelta(months=-prev)
        end_date = timezone.now() if int(prev) == 0 else begin_date + relativedelta(months=1)
        new_real_users = DareyooUser.objects.real().joined_month(prev).count()
        n_users_before = DareyooUser.objects.real().joined_before_month(prev).count()
        new_leads = DareyooUser.objects.all().registered(False).joined_month(prev).count()
        active = DareyooUser.objects.real().active_month().count()
        churn_n = DareyooUser.objects.real().churn_month().count()
        churn = int(round(float(churn_n) / n * 100)) if n > 0 else 0
        new_bets = Bet.objects.all().created_month(prev).count()
        new_basic = Bet.objects.all().created_month(prev).simple().count()
        new_auction = Bet.objects.all().created_month(prev).auction().count()
        new_lottery = Bet.objects.all().created_month(prev).lottery().count()
        new_closed_bets = Bet.objects.all().finished_month(prev).count()
        new_free_coins = int(UserRefill.objects.all().created_month(prev).free().sum())
        new_paying_coins = int(UserRefill.objects.all().created_month(prev).paying().sum())
    active_percent = int(round(float(active) / n * 100)) if n > 0 else 0
    new_percent_basic = int(round(float(new_basic) / new_bets * 100)) if new_bets > 0 else 0
    new_percent_auction = int(round(float(new_auction) / new_bets * 100)) if new_bets > 0 else 0
    new_percent_lottery = int(round(float(new_lottery) / new_bets * 100)) if new_bets > 0 else 0
    new_coins = new_free_coins + new_paying_coins
    percent_new_free_coins = int(round(float(new_free_coins) / new_coins * 100)) if new_coins > 0 else 0
    percent_new_paying_coins = int(round(float(new_paying_coins) / new_coins * 100)) if new_coins > 0 else 0
    burnt_coins = 0
    new_real_users_percent = int(round(float(new_real_users) / max(n_users_before, 1) * 100))

    start_date = timezone.datetime(year=2014, month=10, day=1, tzinfo=pytz.UTC)
    cohort_weeks = rrule.rrule(rrule.WEEKLY, dtstart=start_date, until=timezone.now())
    cohorts = []
    cohort_level = ['login', 'participate', 'create'].index(request.GET.get('activation', 'login'))
    for i in xrange(cohort_weeks.count()):
        current_week = start_date + timezone.timedelta(weeks=cohort_weeks.count()-i)
        wc = weekly_cohort(i, activation_level=cohort_level)
        carray = [{
            'percent': c/float(wc[0]) if wc[0] else 0,
            'total': c,
            'color': int(200 - 200*c/float(wc[0])) if wc[0] else 200
            } for c in wc]
        cohorts.append([current_week.strftime('%d/%m/%Y')] + carray)
    cohorts = reversed(cohorts)
    context = {
        'total_real_users': n,
        'total_fake_users': fake,
        'leads': leads,
        'range': rang,
        'prev': int(prev) + 1,
        'next': int(prev) - 1 if int(prev) > 0 else 0,
        'new_real_users': new_real_users,
        'new_real_users_percent': new_real_users_percent,
        'new_leads': new_leads,
        'active': active,
        'active_percent': active_percent,
        'churn_n': churn_n,
        'churn': churn,
        'total_bets': total_bets,
        'total_basic': total_basic,
        'total_auction': total_auction,
        'total_lottery': total_lottery,
        'percent_basic': percent_basic,
        'percent_auction': percent_auction,
        'percent_lottery': percent_lottery,
        'total_closed_bets': total_closed_bets,
        'percent_closed_bets': percent_closed_bets,
        'begin_date': begin_date,
        'end_date': end_date,
        'new_bets': new_bets,
        'new_basic': new_basic,
        'new_auction': new_auction,
        'new_lottery': new_lottery,
        'new_percent_basic': new_percent_basic,
        'new_percent_auction': new_percent_auction,
        'new_percent_lottery': new_percent_lottery,
        'new_closed_bets': new_closed_bets,
        'total_coins': total_coins,
        'total_coins_available': total_coins_available,
        'total_coins_locked': total_coins_locked,
        'percent_coins_available': percent_coins_available,
        'percent_coins_locked': percent_coins_locked,
        'coins_per_user': coins_per_user,
        'max_coins_per_user': max_coins_per_user,
        'new_free_coins': new_free_coins,
        'new_paying_coins': new_paying_coins,
        'new_coins': new_coins,
        'percent_new_free_coins': percent_new_free_coins,
        'percent_new_paying_coins': percent_new_paying_coins,
        'burnt_coins': burnt_coins,
        'activation': request.GET.get('activation', 'login'),
        'cohorts': cohorts,
    }
    return render_to_response('metrics.html', context_instance=RequestContext(request, context))