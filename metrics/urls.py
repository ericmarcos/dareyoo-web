from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView


urlpatterns = patterns('',
    url(r'^metrics/$', 'metrics.views.main', name="main-metrics"),
    url(r'^new-users/$', 'metrics.views.new_users', name="new-users")
)