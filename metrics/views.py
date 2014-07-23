import re
from django.core.urlresolvers import reverse
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.conf import settings
from django.http import *
from django.shortcuts import render_to_response,redirect, get_object_or_404
from django.template import RequestContext
from django.contrib.auth.decorators import login_required, user_passes_test
from users.models import *
from bets.models import Bet


@user_passes_test(lambda u: u.is_staff)
def main(request):
    n = DareyooUser.objects.n()
    fake = DareyooUser.objects.all().staff().count()
    leads = DareyooUser.objects.all().registered(False).count()
    rang = request.GET.get('range', 'day')
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
    coins_per_user = int(round(float(total_coins) / n * 100)) if n > 0 else 0
    max_coins_per_user = int(DareyooUser.objects.real().order_by('-coins_available')[0].coins_available)
    if rang == 'day':
        new_real_users = DareyooUser.objects.real().joined_day().count()
        new_leads = DareyooUser.objects.all().registered(False).joined_day().count()
        active = DareyooUser.objects.real().active_day().count()
        churn_n = '--'
        churn = '--'
        new_bets = Bet.objects.all().created_day().count()
        new_basic = Bet.objects.all().created_day().simple().count()
        new_auction = Bet.objects.all().created_day().auction().count()
        new_lottery = Bet.objects.all().created_day().lottery().count()
        new_closed_bets = Bet.objects.all().finished_day().count()
        new_free_coins = int(UserRefill.objects.all().created_day().free().sum())
        new_paying_coins = int(UserRefill.objects.all().created_day().paying().sum())
    elif rang == 'week':
        new_real_users = DareyooUser.objects.real().joined_week().count()
        new_leads = DareyooUser.objects.all().registered(False).joined_week().count()
        active = DareyooUser.objects.real().active_week().count()
        churn_n = DareyooUser.objects.real().churn_week().count()
        churn = int(round(float(churn_n) / n * 100)) if n > 0 else 0
        new_bets = Bet.objects.all().created_week().count()
        new_basic = Bet.objects.all().created_week().simple().count()
        new_auction = Bet.objects.all().created_week().auction().count()
        new_lottery = Bet.objects.all().created_week().lottery().count()
        new_closed_bets = Bet.objects.all().finished_week().count()
        new_free_coins = int(UserRefill.objects.all().created_week().free().sum())
        new_paying_coins = int(UserRefill.objects.all().created_week().paying().sum())
    elif rang == 'month':
        new_real_users = DareyooUser.objects.real().joined_month().count()
        new_leads = DareyooUser.objects.all().registered(False).joined_month().count()
        active = DareyooUser.objects.real().active_month().count()
        churn_n = DareyooUser.objects.real().churn_month().count()
        churn = int(round(float(churn_n) / n * 100)) if n > 0 else 0
        new_bets = Bet.objects.all().created_month().count()
        new_basic = Bet.objects.all().created_month().simple().count()
        new_auction = Bet.objects.all().created_month().auction().count()
        new_lottery = Bet.objects.all().created_month().lottery().count()
        new_closed_bets = Bet.objects.all().finished_month().count()
        new_free_coins = int(UserRefill.objects.all().created_month().free().sum())
        new_paying_coins = int(UserRefill.objects.all().created_month().paying().sum())
    active_percent = int(round(float(active) / n * 100)) if n > 0 else 0
    new_percent_basic = int(round(float(new_basic) / new_bets * 100)) if new_bets > 0 else 0
    new_percent_auction = int(round(float(new_auction) / new_bets * 100)) if new_bets > 0 else 0
    new_percent_lottery = int(round(float(new_lottery) / new_bets * 100)) if new_bets > 0 else 0
    new_coins = new_free_coins + new_paying_coins
    percent_new_free_coins = int(round(float(new_free_coins) / new_coins * 100)) if new_coins > 0 else 0
    percent_new_paying_coins = int(round(float(new_paying_coins) / new_coins * 100)) if new_coins > 0 else 0
    burnt_coins = 0
    context = {
        'total_real_users': n,
        'total_fake_users': fake,
        'leads': leads,
        'range': rang,
        'new_real_users': new_real_users,
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
    }
    return render_to_response('metrics.html', context_instance=RequestContext(request, context))