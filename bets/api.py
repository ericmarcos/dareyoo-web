from django.conf.urls import url
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.timezone import now
from haystack.query import SearchQuerySet
from django.core.paginator import Paginator, InvalidPage
from tastypie import fields
#from tastypie.authentication import Authentication
from authentication import OAuth20Authentication
from tastypie.authorization import DjangoAuthorization
from tastypie.authorization import Authorization
from tastypie.exceptions import Unauthorized
from tastypie.resources import ModelResource, trailing_slash
from tastypie.http import HttpGone, HttpMultipleChoices
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from bets.models import *
from users.models import *


class BetsAuthorization(Authorization):
    def read_list(self, object_list, bundle):
        #return object_list
        # This assumes a ``QuerySet`` from ``ModelResource``.
        if bundle.request and bundle.request.user:
            return object_list.filter(user=bundle.request.user)
        else:
            return object_list

    # 
    #def read_detail(self, object_list, bundle):
        # Is the requested object owned by the user?
        #return bundle.obj.user == bundle.request.user

    def create_list(self, object_list, bundle):
        # Assuming their auto-assigned to ``user``.
        return object_list

    def create_detail(self, object_list, bundle):
        #return bundle.obj.user == bundle.request.user
        return True

    def update_list(self, object_list, bundle):
        allowed = []

        # Since they may not all be saved, iterate over them.
        for obj in object_list:
            if obj.user == bundle.request.user:
                allowed.append(obj)

        return allowed

    def update_detail(self, object_list, bundle):
        return bundle.obj.user == bundle.request.user

    def delete_list(self, object_list, bundle):
        # Sorry user, no deletes for you!
        raise Unauthorized("Sorry, no deletes.")

    def delete_detail(self, object_list, bundle):
        raise Unauthorized("Sorry, no deletes.")


class BetResource(ModelResource):
    user = fields.ToOneField('users.api.UserResource', 'user', null=True)
    class Meta:
        queryset = Bet.objects.all()
        resource_name = 'bet'
        list_allowed_methods = ['get', 'post', 'put', 'delete']
        authentication = OAuth20Authentication()
        authorization = BetsAuthorization()
        filtering = {
            "bet_state": ('exact',),
        }

    def prepend_urls(self):
        return [
            url(
                r"^(?P<resource_name>%s)/(?P<pk>\w[\w/-]*)/children%s$" %
                (self._meta.resource_name, trailing_slash()),
                self.wrap_view('get_children'),
                name="api_get_children"
            ),
            url(
                r"^(?P<user_id>me|\d+)/(?P<resource_name>%s)s%s$" %
                (self._meta.resource_name, trailing_slash()),
                self.wrap_view('get_user_bets'),
                name="api_get_user_bets"
            ),
            url(r"^(?P<user_id>me|\d+)/(?P<resource_name>%s)s/(?P<state>%s)%s$" %
                (self._meta.resource_name, "|".join([b[0] for b in BET_STATE_CHOICES]), trailing_slash()),
                self.wrap_view('get_user_bets'),
                name="api_get_user_bets"
            ),
            url(
                r"^(?P<resource_name>%s)/search%s$" %
                (self._meta.resource_name, trailing_slash()),
                self.wrap_view('get_search'),
                name="api_get_search"
            ),
        ]

    def get_children(self, request, **kwargs):
        try:
            obj = self.cached_obj_get_list(request=request, **self.remove_api_resource_names(kwargs))
        except ObjectDoesNotExist:
            return HttpGone()
        except MultipleObjectsReturned:
            return HttpMultipleChoices("More than one resource is found at this URI.")

        #child_resource = ChildResource()
        #return child_resource.get_detail(request, parent_id=obj.pk)

    def get_user_bets(self, request, **kwargs):
        filters = {}
        if kwargs.get('user_id') == 'me':
            filters['user_id'] = request.user
        else:
            filters['user_id'] = kwargs.get('user_id')
        if kwargs.get('state'):
            filters['bet_state'] = kwargs.get('state')
        return self.get_list(request, **filters)

    def get_search(self, request, **kwargs):
        self.method_check(request, allowed=['get'])
        #self.is_authenticated(request)
        self.throttle_check(request)

        # Do the query.
        sqs = SearchQuerySet().models(Bet).load_all().filter(bet_state='bidding').filter(public=True).auto_query(request.GET.get('q', '')).order_by('bidding_deadline')
        paginator = Paginator(sqs, 20)

        try:
            page = paginator.page(int(request.GET.get('page', 1)))
        except InvalidPage:
            raise Http404("Sorry, no results on that page.")

        objects = []

        for result in page.object_list:
            bundle = self.build_bundle(obj=result.object, request=request)
            bundle = self.full_dehydrate(bundle)
            objects.append(bundle)

        object_list = {
            'objects': objects,
        }

        self.log_throttled_access(request)
        return self.create_response(request, object_list)


class BidResource(ModelResource):
    class Meta:
        queryset = Bid.objects.all()
        resource_name = 'bid'
