import re
import json
from django.core.urlresolvers import reverse
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.conf import settings
from django.http import *
from django.shortcuts import render_to_response,redirect, get_object_or_404
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from users.models import DareyooUser
from users.pipelines import *
from bets.models import Bet
from .models import *

def handle_campaign(request):
    #utm_source=google&utm_medium=cpc&utm_campaign=inicial
    source = request.GET.get('utm_source')
    if source:
        request.session['utm_source'] = source
    medium = request.GET.get('utm_medium')
    if source:
        request.session['utm_medium'] = medium
    campaign = request.GET.get('utm_campaign')
    if source:
        request.session['utm_campaign'] = campaign

#TODO: check this for mobile auth:
#https://groups.google.com/forum/#!topic/django-social-auth/zxOVzuQdlDQ
def register_view(request):
    handle_campaign(request)
    if request.user.is_authenticated():
        return HttpResponseRedirect(reverse('beta-home'))
    else:
        context = {'errors':[]}
        if request.POST:
            email = request.POST.get('email', '')
            valid_email = True
            password = request.POST.get('password', '')
            password2 = request.POST.get('password2', '')
            user = DareyooUser.objects.filter(email=email)
            try:
                validate_email(email)
            except ValidationError as e:
                valid_email = False
            if not valid_email:
                context['errors'].append('Please, introduce a valid email')
            elif len(user) > 0 and user[0].registered == True:
                context['errors'].append('This email is already registered')
            elif password != password2:
                context['errors'].append('Wrong password')
            else:
                if len(user) > 0:
                    user = user[0]
                else:
                    #user = DareyooUser.objects.create_user(email, password)
                    user = DareyooUser(email=email)
                    user.set_password(password)
                    user.save()
            #Social pipeline
            pipeline_params = {'strategy': None, 'user': user, 'response':None,
                            'details': None, 'is_new': True, 'request': request}
            save_profile_picture(**pipeline_params)
            save_username(**pipeline_params)
            save_reference_user(**pipeline_params)
            save_registered(**pipeline_params)
            save_campaign(**pipeline_params)
            #promo_code(**pipeline_params)
            #This is kind of a hack... but it works
            #http://stackoverflow.com/questions/15192808/django-automatic-login-after-user-registration-1-4
            user.backend = "django.contrib.auth.backends.ModelBackend"
            login(request, user)
            next_url = request.POST.get('next', reverse('beta-home') + '/edit-profile?new')
            return HttpResponseRedirect(next_url)
        return render_to_response('beta-register.html', context_instance=RequestContext(request, context))


def app(request):
    handle_campaign(request)
    context = {'fb_key': settings.SOCIAL_AUTH_FACEBOOK_KEY}
    #Setting 'from' session, to measure virality
    r = re.search(r'bet/(?P<id>\d*)', request.path)
    if r:
        b = Bet.objects.filter(id=r.group('id'))
        if len(b) > 0: 
            request.session['from'] = b[0].author_id
        fb_useragent = "facebookexternalhit"
        if fb_useragent in request.META['HTTP_USER_AGENT']:
            context['bet'] = b[0] if len(b) > 0 else Bet()
            context['fb_id'] = settings.SOCIAL_AUTH_FACEBOOK_KEY
            return render_to_response('beta-app-bet-fb.html', context_instance=RequestContext(request, context)) 
    return render_to_response('beta-app.html', context_instance=RequestContext(request, context))

def landing_view(request):
    handle_campaign(request)
    bets = Bet.objects.all().bidding().public().extra(where=["CHAR_LENGTH(title) > 50 AND CHAR_LENGTH(title) < 120"]).order_by('?')[:5]
    context = { 'bets': bets }
    return render_to_response('beta-landing.html', context_instance=RequestContext(request, context))

def how_to(request):
    handle_campaign(request)
    return render_to_response('beta-como-funciona.html', context_instance=RequestContext(request))

def faq(request):
    handle_campaign(request)
    return render_to_response('beta-faq.html', context_instance=RequestContext(request))

def mobile_notification(request):
    if request.is_ajax():
        email = request.POST.get('email')
        os = request.POST.get('os')
        MobileNotification.objects.create(email=email, os=os)
        data = json.dumps({'message': "OK"})
        return HttpResponse(data, mimetype='application/json')
    return HttpResponseBadRequest()

def login_error(request):
    return render_to_response('beta-login-error.html', context_instance=RequestContext(request))

def campaign_ny2015_view(request):
    handle_campaign(request)
    context = {'fb_key': settings.SOCIAL_AUTH_FACEBOOK_KEY}
    return render_to_response('new-year-2015-campaign-landing.html', context_instance=RequestContext(request, context))
