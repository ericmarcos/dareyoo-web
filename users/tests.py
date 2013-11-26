import datetime
from django.contrib.auth import get_user_model
from provider.oauth2 import models
from tastypie.test import ResourceTestCase
from users.models import DareyooUser
from django.test.client import Client


class UserResourceTest(ResourceTestCase):
    # Use ``fixtures`` & ``urls`` as normal. See Django's ``TestCase``
    # documentation for the gory details.
    fixtures = ['test_data.json']

    def setUp(self):
        super(UserResourceTest, self).setUp()
        self.maxDiff = None
        # Create a user.
        self.username = 'eric-test'
        self.email = 'eric-test@dareyoo.net'
        self.password = 'pass'
        self.user = DareyooUser.objects.create_user(self.email, self.password)
        self.user.username = self.username
        self.user.save()

        # We also build a detail URI, since we will be using it all over.
        # DRY, baby. DRY.
        self.detail_url = '/api/v1/user/{0}/'
        self.oauth_token_url = '/oauth2/access_token'

        self.client = models.Client(
            user=self.user,
            url="www.dareyoo.net",
            redirect_uri="www.dareyoo.net/redirect",
            client_type=1
        )
        self.client.save()

    def get_oauth2_token(self):
        data = {
            u'client_id':unicode(self.client.client_id),
            u'client_secret':unicode(self.client.client_secret),
            u'grant_type':u'password',
            u'username':unicode(self.email),
            u'password':unicode(self.password),
            u'scope':u'write'
        }
        c = Client()
        resp = c.post(self.oauth_token_url, data)
        self.token = self.deserialize(resp)['access_token']

    def create_oauth2(self):
        return 'OAuth %s' % self.token

    def test_get_oauth_token(self):
        # curl -d "client_id=ce922218a456cac00a53&client_secret=29da6be31d993b3e7890da3de531bdaac60ed50f&grant_type=password&email=ericmarcos.p@gmail.com&password=1234&scope=write" http://localhost:8000/oauth2/access_token
        # curl -v -H "Authorization: OAuth 5fb02f42decc4fe3b357adfebfffab1c21fd2750" http://127.0.0.1:8000/api/v1/bet/?format=json
        data = {
            'client_id':self.client.client_id,
            'client_secret':self.client.client_secret,
            'grant_type':'password',
            'username':self.email,
            'password':self.password,
            'scope':'write'
        }
        #resp = self.api_client.post(self.oauth_token_url, format='json', data=data)
        c = Client()
        resp = c.post(self.oauth_token_url, data)
        self.assertValidJSONResponse(resp)
        keys = [u'access_token', u'scope', u'expires_in', u'refresh_token']
        self.assertKeys(self.deserialize(resp), keys)
        self.assertEqual(self.deserialize(resp)['scope'], u'read write read+write')
        self.token = self.deserialize(resp)['access_token']
        #Testing that the token actually works to get some data
        resp = self.api_client.get(self.detail_url.format(self.user.pk), format='json', authentication=self.create_oauth2())
        self.assertValidJSONResponse(resp)

    def test_get_followers(self):
        self.get_oauth2_token()
        resp = self.api_client.get(self.detail_url.format(1) + 'followers/', format='json', authentication=self.create_oauth2())
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 3)
        self.assertEqual([u['username'] for u in self.deserialize(resp)['objects']], [u'josep', u'franzi', u'superman'])

    def test_get_following(self):
        self.get_oauth2_token()
        resp = self.api_client.get(self.detail_url.format(4) + 'following/', format='json', authentication=self.create_oauth2())
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 3)
        self.assertEqual([u['username'] for u in self.deserialize(resp)['objects']], [u'eric', u'josep', u'franzi'])

    def test_follow_unfollow_unauthorized(self):
        ''' Testing that the logged in user can't change the following of other users '''
        self.get_oauth2_token()
        data = {'action':'add', 'user_id':1}
        resp = self.api_client.post(self.detail_url.format(3) + 'followers/', data=data, authentication=self.create_oauth2())
        self.assertHttpForbidden(resp)
        data = {'action':'remove', 'user_id':3}
        resp = self.api_client.post(self.detail_url.format(1) + 'followers/', data=data, authentication=self.create_oauth2())
        self.assertHttpForbidden(resp)

    def test_follow_yourself_forbidden(self):
        self.get_oauth2_token()
        data = {'action':'add', 'user_id':self.user.id}
        resp = self.api_client.post(self.detail_url.format(self.user.id) + 'followers/', format='json', data=data, authentication=self.create_oauth2())
        self.assertHttpBadRequest(resp)

    def test_follow_unfollow(self):
        self.get_oauth2_token()
        # Checking initial data (3 followrs for user 1)
        resp = self.api_client.get(self.detail_url.format(1) + 'followers/', format='json', authentication=self.create_oauth2())
        self.assertEqual(len(self.deserialize(resp)['objects']), 3)
        # Adding the authenticated user as a follower of user 1
        data = {'action':'add', 'user_id':self.user.id}
        resp = self.api_client.post(self.detail_url.format(1) + 'followers/', data=data, authentication=self.create_oauth2())
        self.assertHttpCreated(resp)
        # Checking that it actually added a follower
        resp = self.api_client.get(self.detail_url.format(1) + 'followers/', format='json', authentication=self.create_oauth2())
        self.assertEqual(len(self.deserialize(resp)['objects']), 4)
        # Checking that following again doesn't add it again
        resp = self.api_client.post(self.detail_url.format(1) + 'followers/', data=data, authentication=self.create_oauth2())
        self.assertHttpCreated(resp)
        resp = self.api_client.get(self.detail_url.format(1) + 'followers/', format='json', authentication=self.create_oauth2())
        self.assertEqual(len(self.deserialize(resp)['objects']), 4)
        # Unfollowing
        data = {'action':'remove', 'user_id':self.user.id}
        resp = self.api_client.post(self.detail_url.format(1) + 'followers/', data=data, authentication=self.create_oauth2())
        self.assertHttpCreated(resp)
        # Checking that it actually removed a follower
        resp = self.api_client.get(self.detail_url.format(1) + 'followers/', format='json', authentication=self.create_oauth2())
        self.assertEqual(len(self.deserialize(resp)['objects']), 3)
        # Checking that unfollowing again doesn't cause any trouble
        resp = self.api_client.post(self.detail_url.format(1) + 'followers/', data=data, authentication=self.create_oauth2())
        self.assertHttpCreated(resp)
        resp = self.api_client.get(self.detail_url.format(1) + 'followers/', format='json', authentication=self.create_oauth2())
        self.assertEqual(len(self.deserialize(resp)['objects']), 3)
