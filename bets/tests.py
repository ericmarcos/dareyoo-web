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

    def test_get_bet_list(self):
        self.assertEqual(0, 1)

    def test_get_bet_detail(self):
        self.assertEqual(0, 1)

    def test_create_bet(self):
        self.assertEqual(0, 1)

    def test_update_bet(self):
        self.assertEqual(0, 1)

    def test_update_bet_unauthorised(self):
        self.assertEqual(0, 1)

    def test_delete_bet(self):
        self.assertEqual(0, 1)

    def test_delete_bet_unauthorised(self):
        self.assertEqual(0, 1)

    def test_accept_simple_bet(self):
        self.assertEqual(0, 1)

    def test_resolve_simple_bet(self):
        self.assertEqual(0, 1)

    def test_conflict_simple_bet(self):
        self.assertEqual(0, 1)