from django.conf.urls import patterns, url
from django.views.generic import TemplateView

urlpatterns = patterns('_templateapp.views',
    url(r'^$', TemplateView.as_view(template_name="index.html"), name='home'),
    url(r'^example$', 'example', name='example'),
)