from tastypie.resources import ModelResource, trailing_slash
from users.models import *
from django.conf.urls import url
from django.conf import settings
from django.utils.timezone import now
from django.core.urlresolvers import reverse
from django.http import Http404
from authentication import OAuth20Authentication
from tastypie.authentication import Authentication
from tastypie.authorization import DjangoAuthorization
from tastypie.http import HttpGone, HttpMultipleChoices, HttpCreated, HttpBadRequest, HttpForbidden
from tastypie import fields
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.core.paginator import Paginator, InvalidPage
from django.shortcuts import get_object_or_404
from tastypie.exceptions import ImmediateHttpResponse

class UserResource(ModelResource):
    n_following = fields.IntegerField(attribute='n_following')
    n_followers = fields.IntegerField(attribute='n_followers')

    class Meta:
        queryset = DareyooUser.objects.all()
        resource_name = 'user'
        authentication = OAuth20Authentication()
        #authentication = Authentication()
        authorization = DjangoAuthorization()
        fields = ['username', 'first_name', 'last_name', 'last_login']
        allowed_methods = ['get']

    def prepend_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/(?P<pk>\w[\w/-]*)/followers%s$" %
                (self._meta.resource_name, trailing_slash()),
                self.wrap_view('dispatch_followers'), name="api_dispatch_followers"),
            url(r"^(?P<resource_name>%s)/(?P<pk>\w[\w/-]*)/following%s$" %
                (self._meta.resource_name, trailing_slash()),
                self.wrap_view('dispatch_following'), name="api_dispatch_following"),
            url(r"^(?P<resource_name>%s)/refill%s$" %
                (self._meta.resource_name, trailing_slash()), self.wrap_view('post_refill'), name="api_post_refill"),
        ]

    def dispatch_followers(self, request, **kwargs):
        self.method_check(request, allowed=['get', 'post'])
        self.is_authenticated(request)
        self.throttle_check(request)

        basic_bundle = self.build_bundle(request=request)
        try:
            obj = self.cached_obj_get(bundle=basic_bundle, **self.remove_api_resource_names(kwargs))
        except ObjectDoesNotExist:
            return HttpGone()
        except MultipleObjectsReturned:
            return HttpMultipleChoices("More than one resource is found at this URI.")
        if request.method == "POST":
            post = request.POST or self.deserialize(request, request.body, format=request.META.get('CONTENT_TYPE', 'application/json'))
            if  post.get('action') == "add":
                u = get_object_or_404(DareyooUser, pk=post.get('user_id'))
                if u.id == obj.id:
                    raise ImmediateHttpResponse(HttpBadRequest())
                if u.id != request.user.id:
                    raise ImmediateHttpResponse(HttpForbidden())
                obj.followers.add(u)
                raise ImmediateHttpResponse(HttpCreated())

            elif post.get('action') == "remove":
                u = get_object_or_404(DareyooUser, pk=post.get('user_id'))
                if u.id == obj.id:
                    raise ImmediateHttpResponse(HttpBadRequest())
                if u.id != request.user.id:
                    raise ImmediateHttpResponse(HttpForbidden())
                obj.followers.remove(u)
                raise ImmediateHttpResponse(HttpCreated())

            else:
                raise ImmediateHttpResponse(HttpForbidden("No action set"))
            
        elif request.method == "GET":
            following = DareyooUser.objects.filter(following=obj)
            paginator = Paginator(following, 20)

            try:
                page = paginator.page(int(request.GET.get('page', 1)))
            except InvalidPage:
                raise Http404("Sorry, no results on that page.")

            objects = []

            for result in page.object_list:
                bundle = self.build_bundle(obj=result, request=request)
                bundle = self.full_dehydrate(bundle)
                objects.append(bundle)

            object_list = {
                'objects': objects,
            }

            self.log_throttled_access(request)
            return self.create_response(request, object_list)

    def dispatch_following(self, request, **kwargs):
        basic_bundle = self.build_bundle(request=request)
        try:
            obj = self.cached_obj_get(bundle=basic_bundle, **self.remove_api_resource_names(kwargs))
        except ObjectDoesNotExist:
            return HttpGone()
        except MultipleObjectsReturned:
            return HttpMultipleChoices("More than one resource is found at this URI.")

        self.method_check(request, allowed=['get'])
        self.is_authenticated(request)
        self.throttle_check(request)

        followers = DareyooUser.objects.filter(followers=obj)
        paginator = Paginator(followers, 20)

        try:
            page = paginator.page(int(request.GET.get('page', 1)))
        except InvalidPage:
            raise Http404("Sorry, no results on that page.")

        objects = []

        for result in page.object_list:
            bundle = self.build_bundle(obj=result, request=request)
            bundle = self.full_dehydrate(bundle)
            objects.append(bundle)

        object_list = {
            'objects': objects,
        }

        self.log_throttled_access(request)
        return self.create_response(request, object_list)

    def post_refill(self, request, **kwargs):
        self.method_check(request, allowed=['post'])
        self.is_authenticated(request)
        self.throttle_check(request)

        if request.user and len(UserRefill.objects.filter(user=request.user, date__gt=now() - settings.MIN_FREE_REFILL_PERIOD)) == 0:
            request.user.refill(settings.FREE_REFILL_AMOUNT, 'free')
        else:
            raise ImmediateHttpResponse(HttpForbidden())

        bundle = self.build_bundle(obj=request.user, request=request)
        bundle = self.full_dehydrate(bundle)

        object_list = {
            'objects': [bundle],
        }

        self.log_throttled_access(request)
        return self.create_response(request, object_list)
