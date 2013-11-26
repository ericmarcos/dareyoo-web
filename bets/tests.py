import datetime
from django.contrib.auth import get_user_model
from provider.oauth2.models import AccessToken, Client
from tastypie.test import ResourceTestCase
from bets.models import Bet, Bid
from bets.api import BetsAuthorization


class BetResourceTest(ResourceTestCase):
    # Use ``fixtures`` & ``urls`` as normal. See Django's ``TestCase``
    # documentation for the gory details.
    fixtures = ['test_data.json']

    def setUp(self):
        super(BetResourceTest, self).setUp()
        self.maxDiff = None
        # Create a user.
        self.username = 'eric-test'
        self.email = 'eric-test@dareyoo.net'
        self.password = 'pass'
        self.user = get_user_model().objects.create_user(self.email, self.password)
        self.user.username = self.username

        # Fetch the Bet object we'll use in testing.
        # Note that we aren't using PKs because they can change depending
        # on what other tests are running.
        self.bet_1 = Bet.objects.get(title='TestBet1')
        self.bet_1.user = self.user
        self.bet_1.save()

        # We also build a detail URI, since we will be using it all over.
        # DRY, baby. DRY.
        self.detail_url = '/api/v1/bet/{0}/'.format(self.bet_1.pk)

        # The data we'll send on POST requests. Again, because we'll use it
        # frequently (enough).
        self.post_data = {
            u'amount': 50.0,
            u'bet_state': u'bidding',
            u'bidding_deadline': u'2014-06-26T23:51:06+00:00',
            u'claim': None,
            u'description': u'This is a test Bet POST',
            u'event_deadline': u'2014-06-27T01:51:17+00:00',
            u'public': True,
            u'tags': u'tv series',
            u'title': u'TestBetPost'
        }
        client = Client(
            user=self.user,
            url="www.dareyoo.net",
            redirect_uri="www.dareyoo.net/redirect",
            client_type=0
        )
        client.save()

        self.token = AccessToken.objects.create(
            user=self.user,
            client=client,
            scope=6
        )

    def get_credentials(self):
        return self.create_oauth2(self.email, self.password)

    def create_oauth2(self, email, password):
        return 'OAuth %s' % self.token.token

    def test_get_list_unauthorzied(self):
        self.assertHttpUnauthorized(self.api_client.get('/api/v1/bet/', format='json'))

    def test_get_list_json(self):
        resp = self.api_client.get('/api/v1/bet/', format='json', authentication=self.get_credentials())
        self.assertValidJSONResponse(resp)

        # Scope out the data for correctness.
        self.assertEqual(len(self.deserialize(resp)['objects']), 1)
        # Here, we're checking an entire structure for the expected data.
        self.assertEqual(self.deserialize(resp)['objects'][0], {
            u'amount': 60.0,
            u'bet_state': u'bidding',
            u'bidding_deadline': u'2013-06-26T23:51:06',
            u'claim': None,
            u'created_at': u'2013-05-26T16:51:36.416000',
            u'description': u'This is a test Bet',
            u'event_deadline': u'2013-06-27T01:51:17',
            u'id': 1,
            u'public': True,
            u'resource_uri': u'/api/v1/bet/{0}/'.format(self.bet_1.pk),
            u'tags': u'sports tennis',
            u'title': u'TestBet1',
            u'user': u'/api/v1/user/{0}/'.format(self.user.pk)
        })

    def test_get_detail_unauthenticated(self):
        self.assertHttpUnauthorized(self.api_client.get(self.detail_url, format='json'))

    def test_get_detail_json(self):
        resp = self.api_client.get(self.detail_url, format='json', authentication=self.get_credentials())
        self.assertValidJSONResponse(resp)

        # We use ``assertKeys`` here to just verify the keys, not all the data.
        keys = [u'amount', u'bet_state', u'bidding_deadline',
            u'claim', u'created_at', u'description', u'event_deadline',
            u'id', u'public', u'resource_uri', u'tags', u'title', u'user']
        self.assertKeys(self.deserialize(resp), keys)
        self.assertEqual(self.deserialize(resp)['description'], u'This is a test Bet')

    def test_post_list_unauthenticated(self):
        self.assertHttpUnauthorized(self.api_client.post('/api/v1/bet/', format='json', data=self.post_data))

    def test_post_list(self):
        # Check how many are there first.
        self.assertEqual(Bet.objects.count(), 1)
        self.assertHttpCreated(self.api_client.post('/api/v1/bet/', format='json', data=self.post_data, authentication=self.get_credentials()))
        # Verify a new one has been added.
        self.assertEqual(Bet.objects.count(), 2)

    def test_put_detail_unauthenticated(self):
        self.assertHttpUnauthorized(self.api_client.put(self.detail_url, format='json', data={}))

    def test_put_detail(self):
        # Grab the current data & modify it slightly.
        original_data = self.deserialize(self.api_client.get(self.detail_url, format='json', authentication=self.get_credentials()))
        new_data = original_data.copy()
        new_data['title'] = 'Updated: This is a test Bet'
        new_data['amount'] = 100

        self.assertEqual(Bet.objects.count(), 1)
        self.assertHttpAccepted(self.api_client.put(self.detail_url, format='json', data=new_data, authentication=self.get_credentials()))
        # Make sure the count hasn't changed & we did an update.
        self.assertEqual(Bet.objects.count(), 1)
        # Check for updated data.
        self.assertEqual(Bet.objects.get(pk=1).title, 'Updated: This is a test Bet')
        self.assertEqual(Bet.objects.get(pk=1).amount, 100)

    def test_delete_detail_unauthenticated(self):
        self.assertHttpUnauthorized(self.api_client.delete(self.detail_url, format='json'))

    def test_delete_detail(self):
        self.assertEqual(Bet.objects.count(), 1)
        # Deletes are not allowed (even if the user is authenticated)
        self.assertHttpUnauthorized(self.api_client.delete(self.detail_url, format='json', authentication=self.get_credentials()))
        # Checking that it actually didn't delete the object
        self.assertEqual(Bet.objects.count(), 1)

    def test_get_bids(self):
        original_data = self.deserialize(self.api_client.get(self.detail_url, format='json', authentication=self.get_credentials()))