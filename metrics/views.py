import re
from django.core.urlresolvers import reverse
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.conf import settings
from django.http import *
from django.shortcuts import render_to_response,redirect, get_object_or_404
from django.template import RequestContext
from django.contrib.auth.decorators import login_required, user_passes_test
from users.models import DareyooUser
from bets.models import Bet


@user_passes_test(lambda u: u.is_staff)
def main(request):
    n = DareyooUser.objects.n()
    fake = DareyooUser.objects.all().staff().count()
    leads = DareyooUser.objects.all().registered(False).count()
    context = {
        'total_real_users': n,
        'total_fake_users': fake,
        'total_users': n + fake,
        'leads': leads,
    }
    return render_to_response('metrics.html', context_instance=RequestContext(request, context))