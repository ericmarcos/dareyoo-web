from django.shortcuts import render_to_response
from django.template import RequestContext


def example(request):
    context = {'extra_content': "You're in the example view."}
    return render_to_response('index.html', RequestContext(request, context))