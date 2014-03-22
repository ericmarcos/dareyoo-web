from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('beta.views',
    url(r'^$', 'landing_view', name='beta-landing'),
    url(r'^login$', 'login_view', name='beta-login'),
    url(r'^logout$', 'logout_view', name='beta-logout'),
    url(r'^app$', 'app', name='beta-home'),
)