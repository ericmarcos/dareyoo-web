import re
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

#TODO: check this for mobile auth:
#https://groups.google.com/forum/#!topic/django-social-auth/zxOVzuQdlDQ
def register_view(request):
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
                #This is kind of a hack... but it works
                #http://stackoverflow.com/questions/15192808/django-automatic-login-after-user-registration-1-4
                user.backend = "django.contrib.auth.backends.ModelBackend"
                login(request, user)
                return HttpResponseRedirect(reverse('beta-home') + '/edit-profile?new')
        return render_to_response('beta-register.html', context_instance=RequestContext(request, context))


def app(request):
    context = {'fb_key': settings.SOCIAL_AUTH_FACEBOOK_KEY}
    #Setting 'from' session, to measure virality
    r = re.search(r'bet/(?P<id>\d*)', request.path)
    if r:
        bet = get_object_or_404(Bet, r.group('id'))
        request.session['from'] = bet.author_id
        fb_useragent = "facebookexternalhit"
        if fb_useragent in request.META['HTTP_USER_AGENT']:
            context['bet'] = bet
            context['fb_id'] = settings.SOCIAL_AUTH_FACEBOOK_KEY
            return render_to_response('beta-app-bet-fb.html', context_instance=RequestContext(request, context)) 
    return render_to_response('beta-app.html', context_instance=RequestContext(request, context))

def landing_view(request):
    return render_to_response('beta-landing.html', context_instance=RequestContext(request))