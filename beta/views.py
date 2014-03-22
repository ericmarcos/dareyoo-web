from django.core.urlresolvers import reverse
from django.http import *
from django.shortcuts import render_to_response,redirect
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout

def login_view(request):
    if request.user.is_authenticated():
        return HttpResponseRedirect(reverse('beta-home'))
    else:
        params = {'errors':[]}
        if request.POST:
            username = request.POST.get('username', '')
            password = request.POST.get('password', '')
            user = authenticate(username=username, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    return HttpResponseRedirect(reverse('beta-home'))
            params['errors'].append('Invalid username or password')
        return render_to_response('beta-landing.html', context_instance=RequestContext(request, params))


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse('beta-landing'))
 
#@login_required(login_url=reverse('alpha-login')) # Error: causes a circular dependency
def app(request):
    return render_to_response('beta-app.html', context_instance=RequestContext(request))

def landing_view(request):
    return render_to_response('beta-landing.html', context_instance=RequestContext(request))