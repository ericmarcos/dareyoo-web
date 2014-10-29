import datetime
import json
from django.core.urlresolvers import reverse
from django.contrib.auth import get_user_model
from provider.oauth2 import models
from tastypie.test import ResourceTestCase
from rest_framework.test import APITestCase
from rest_framework import status
from users.models import DareyooUser
from django.test.client import Client


class UserResourceTest(APITestCase):
    # Use ``fixtures`` & ``urls`` as normal. See Django's ``TestCase``
    # documentation for the gory details.
    #fixtures = ['test_data.json']
    
    def setUp(self):
        super(APITestCase, self).setUp()
        # Create a user.
        self.username = 'eric-test'
        self.email = 'eric-test@dareyoo.net'
        self.password = 'pass'
        self.user = DareyooUser.objects.create_user(self.email, self.password)
        self.user.username = self.username
        self.user.save()

        self.oauth_token_url = '/oauth2/access_token'

        self.api_client = models.Client(
            user=self.user,
            url="www.dareyoo.net",
            redirect_uri="www.dareyoo.net/redirect",
            client_type=1
        )
        self.api_client.save()
    
    def get_oauth2_token(self):
        data = {
            u'client_id':unicode(self.api_client.client_id),
            u'client_secret':unicode(self.api_client.client_secret),
            u'grant_type':u'password',
            u'username':unicode(self.email),
            u'password':unicode(self.password),
            u'scope':u'write'
        }
        resp = self.client.post(self.oauth_token_url, data)
        self.token = json.loads(resp.content)['access_token']
        return self.create_oauth2()

    def create_oauth2(self):
        #return 'OAuth %s' % self.token
        return 'Bearer %s' % self.token

    def test_get_oauth_token(self):
        data = {
            'client_id':self.api_client.client_id,
            'client_secret':self.api_client.client_secret,
            'grant_type':'password',
            'username':self.email,
            'password':self.password,
            'scope':'write'
        }
        resp = self.client.post(self.oauth_token_url, data)
        data = json.loads(resp.content)
        keys = [u'access_token', u'scope', u'expires_in', u'refresh_token']
        self.assertEqual(data['scope'], 'read write read+write')
        self.token = data['access_token']

    def test_get_followers(self):
        resp = self.client.get(reverse('dareyoouser-followers', args=[1]), format='json')
        self.assertEqual(len(resp.data), 3)
        self.assertEqual([u['username'] for u in resp.data], ['josep', 'franzi', 'superman'])

    def test_get_following(self):
        resp = self.client.get(reverse('dareyoouser-following', args=[4]))
        self.assertEqual(len(resp.data), 3)
        self.assertEqual([u['username'] for u in resp.data], ['eric', 'josep', 'franzi'])
    
    def test_follow_unfollow_unauthorized(self):
        ''' Testing that the logged in user can't change the following of other users '''
        #Getting credentials for user 5
        self.client.credentials(HTTP_AUTHORIZATION=self.get_oauth2_token())

        data = {'user_id': 1}
        resp = self.client.post(reverse('dareyoouser-follow', args=[3]), data)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        data = {'user_id': 3}
        resp = self.client.delete(reverse('dareyoouser-unfollow', args=[1]), data)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        self.client.credentials()

    def test_follow_yourself_forbidden(self):
        self.client.credentials(HTTP_AUTHORIZATION=self.get_oauth2_token())

        data = {'user_id': self.user.id}
        resp = self.client.post(reverse('dareyoouser-follow', args=[self.user.id]), data)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

        self.client.credentials()
    
    def test_follow_unfollow(self):
        #Getting credentials for user 5
        self.client.credentials(HTTP_AUTHORIZATION=self.get_oauth2_token())

        # Checking initial data (3 followrs for user 1)
        resp = self.client.get(reverse('dareyoouser-followers', args=[1]), format='json')
        self.assertEqual(len(resp.data), 3)
        
        # Adding the authenticated user as a follower of user 1
        data = {'user_id': 1}
        resp = self.client.post(reverse('dareyoouser-follow', args=[self.user.id]), data)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        # Checking that it actually added a follower
        resp = self.client.get(reverse('dareyoouser-followers', args=[1]), format='json')
        self.assertEqual(len(resp.data), 4)
        
        # Checking that following again doesn't add it again
        data = {'user_id': 1}
        resp = self.client.post(reverse('dareyoouser-follow', args=[self.user.id]), data)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        resp = self.client.get(reverse('dareyoouser-followers', args=[1]), format='json')
        self.assertEqual(len(resp.data), 4)

        # Unfollowing
        data = {'user_id': 1}
        resp = self.client.delete(reverse('dareyoouser-unfollow', args=[self.user.id]), data)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

        # Checking that it actually removed a follower
        resp = self.client.get(reverse('dareyoouser-followers', args=[1]), format='json')
        self.assertEqual(len(resp.data), 3)

        # Checking that unfollowing again doesn't cause any trouble
        data = {'user_id': 1}
        resp = self.client.delete(reverse('dareyoouser-unfollow', args=[self.user.id]), data)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        resp = self.client.get(reverse('dareyoouser-followers', args=[1]), format='json')
        self.assertEqual(len(resp.data), 3)

        #Unsetting credentials for future tests
        self.client.credentials()