#import datetime
import json
from mock import Mock
from celery import current_app as celery
from django.core.urlresolvers import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
#from django.test.utils import override_settings
from rest_framework.test import APITestCase
from rest_framework import status
from provider.oauth2.models import Client
from bets.models import Bet, Bid


class BetResourceTest(APITestCase):
    # Use ``fixtures`` & ``urls`` as normal. See Django's ``TestCase``
    # documentation for the gory details.
    #fixtures = ['test_data.json']

    def future(self, minutes=0):
        return timezone.now() + timezone.timedelta(minutes=minutes)

    def time_machine(self, minutes=0):
        if not getattr(self, 'original_now', False):
            self.original_now = timezone.now
        timezone.now = lambda: self.original_now() + timezone.timedelta(minutes=minutes)

    def setUp(self):
        super(BetResourceTest, self).setUp()

        celery.send_task = Mock()

        self.username_1 = 'test_user_1'
        self.email_1 = 'test_user_1@dareyoo.net'
        self.password_1 = 'pass'
        self.user_1 = get_user_model().objects.create_user(self.username_1, self.email_1, self.password_1)

        self.username_2 = 'test_user_2'
        self.email_2 = 'test_user_2@dareyoo.net'
        self.password_2 = 'pass'
        self.user_2 = get_user_model().objects.create_user(self.username_2, self.email_2, self.password_2)

        self.username_3 = 'test_user_3'
        self.email_3 = 'test_user_3@dareyoo.net'
        self.password_3 = 'pass'
        self.user_3 = get_user_model().objects.create_user(self.username_3, self.email_3, self.password_3)

        self.username_4 = 'test_user_4'
        self.email_4 = 'test_user_4@dareyoo.net'
        self.password_4 = 'pass'
        self.user_4 = get_user_model().objects.create_user(self.username_4, self.email_4, self.password_4)

        self.username_5 = 'test_user_5'
        self.email_5 = 'test_user_5@dareyoo.net'
        self.password_5 = 'pass'
        self.user_5 = get_user_model().objects.create_user(self.username_5, self.email_5, self.password_5)

        self.api_client = Client.objects.create(
            url="www.dareyoo.com",
            redirect_uri="www.dareyoo.com/redirect",
            client_type=1
        )

        self.url_get_token = reverse('oauth2:access_token')
        self.url_post_bet = reverse('bet-list')

    def login(self, user_i):
        get_token_data = {
            'client_id': self.api_client.client_id,
            'client_secret': self.api_client.client_secret,
            'grant_type': 'password',
            'username': getattr(self, "email_%i" % user_i),
            'password': getattr(self, "password_%i" % user_i),
            'scope': 'write'
        }
        response_token = self.client.post(self.url_get_token, get_token_data)
        response_token_json = json.loads(response_token.content)
        token = response_token_json['access_token']

        self.client.credentials(HTTP_AUTHORIZATION='Bearer %s' % token)

    def logout(self):
        self.client.credentials()

    def test_lottery_arbitrage1(self):

        ###### Creating lottery with user 1
        self.login(1)

        bet_count = Bet.objects.count()
        post_bet_data = {
            'amount': 50.0,
            'bet_type': 3,
            'bidding_deadline': self.future(15),
            'description': 'This is a test Bet POST',
            'event_deadline': self.future(30),
            'public': True,
            'title': 'TestBetPost'
        }
        response_post_bet = self.client.post(self.url_post_bet, post_bet_data)
        self.assertEqual(Bet.objects.count(), bet_count + 1)

        bet = Bet.objects.last()
        self.assertEqual(bet.title, post_bet_data.get('title'))
        self.assertEqual(bet.bet_state, "bidding")

        ####### Creating some results with user 1
        url_post_bid = reverse('bet-bids', args=(bet.id,))

        post_bid_data = {
            'title': "TestBid1"
        }
        response_post_bid = self.client.post(url_post_bid, post_bid_data)
        self.assertEqual(bet.bids.count(), 1)
        bid_1 = Bid.objects.last()
        self.assertEqual(response_post_bid.data.get('title'), bid_1.title)

        post_bid_data = {
            'title': "TestBid2"
        }
        response_post_bid = self.client.post(url_post_bid, post_bid_data)
        self.assertEqual(bet.bids.count(), 2)
        bid_2 = Bid.objects.last()
        self.assertEqual(response_post_bid.data.get('title'), bid_2.title)

        post_bid_data = {
            'title': "TestBid3"
        }
        response_post_bid = self.client.post(url_post_bid, post_bid_data)
        self.assertEqual(bet.bids.count(), 3)
        bid_3 = Bid.objects.last()
        self.assertEqual(response_post_bid.data.get('title'), bid_3.title)

        ####### Participating in first result with user 2
        self.login(2)

        url_post_bid_participant = reverse('bid-add-participant', args=(bid_1.id,))
        response_post_bid_participant = self.client.post(url_post_bid_participant)
        self.assertEqual(bid_1.participants.count(), 1)

        url_get_bid_participants = reverse('bid-participants', args=(bid_1.id,))
        response_get_bid_participants = self.client.get(url_get_bid_participants)
        self.assertEqual(len(response_get_bid_participants.data), 1)
        self.assertEqual(response_get_bid_participants.data[0]['username'], self.username_2)

        ####### Participating in second result with user 3
        self.login(3)

        url_post_bid_participant = reverse('bid-add-participant', args=(bid_2.id,))
        response_post_bid_participant = self.client.post(url_post_bid_participant)
        self.assertEqual(bid_2.participants.count(), 1)

        url_get_bid_participants = reverse('bid-participants', args=(bid_2.id,))
        response_get_bid_participants = self.client.get(url_get_bid_participants)
        self.assertEqual(len(response_get_bid_participants.data), 1)
        self.assertEqual(response_get_bid_participants.data[0]['username'], self.username_3)

        ####### Going to event state
        self.time_machine(16)
        bet.next_state()
        self.assertEqual(bet.bet_state, "event")

        ####### Going to resolving state
        self.time_machine(31)
        bet.next_state()
        self.assertEqual(bet.bet_state, "resolving")

        ###### Resolving bet with user 1 (resolving to "nobody won")
        self.login(1)
        url_post_bet_resolve = reverse('bet-resolve', args=(bet.id,))
        post_resolve_data = {
            'claim': 3,
            'claim_message': "ClaimMessageTest"
        }
        response_post_bet_resolve = self.client.post(url_post_bet_resolve, post_resolve_data)
        bet = Bet.objects.get(id=bet.id)
        self.assertEqual(bet.bet_state, "complaining")

        ###### Complaining bet with user 2 (complaining that result 1 is the winner)
        self.login(2)
        url_post_bet_complain = reverse('bid-complain', args=(bid_1.id,))
        post_complain_data = {
            'claim': 2,
            'claim_message': "ClaimComplainMessageTest"
        }
        response_post_bet_complain = self.client.post(url_post_bet_complain, post_complain_data)
        bet = Bet.objects.get(id=bet.id)
        self.assertEqual(bet.bet_state, "arbitrating")

        ###### Arbitrating bet with user 5 (arbitrating in favour of user 2, so result 1 is the actual winner)
        self.login(5)
        url_post_bet_arbitrate = reverse('bet-arbitrate', args=(bet.id,))
        post_arbitrate_data = {
            'claim_lottery_winner': 1,
            'claim_message': "ClaimArbitrateMessageTest"
        }
        response_post_bet_arbitrate = self.client.post(url_post_bet_arbitrate, post_arbitrate_data)
        bet = Bet.objects.get(id=bet.id)
        self.assertEqual(bet.bet_state, "closed")

        ####### User 5 should get the most points for arbitrating,
        ####### then user 2 for winning the lottery, then user 3 for participating
        ####### and finally user 1 with negative points for losing the conflict
        ranking = [self.username_5, self.username_2, self.username_3, self.username_1]
        self.assertEqual([p.user.username for p in bet.points.all().order_by('-points')], ranking)

        self.logout()

    def test_lottery_arbitrage2(self):

        ###### Creating lottery with user 1
        self.login(1)

        bet_count = Bet.objects.count()
        post_bet_data = {
            'amount': 50.0,
            'bet_type': 3,
            'bidding_deadline': self.future(15),
            'description': 'This is a test Bet POST',
            'event_deadline': self.future(30),
            'public': True,
            'title': 'TestBetPost'
        }
        response_post_bet = self.client.post(self.url_post_bet, post_bet_data)
        self.assertEqual(Bet.objects.count(), bet_count + 1)

        bet = Bet.objects.last()
        self.assertEqual(bet.title, post_bet_data.get('title'))
        self.assertEqual(bet.bet_state, "bidding")

        ####### Creating some results with user 1
        url_post_bid = reverse('bet-bids', args=(bet.id,))

        post_bid_data = {
            'title': "TestBid1"
        }
        response_post_bid = self.client.post(url_post_bid, post_bid_data)
        self.assertEqual(bet.bids.count(), 1)
        bid_1 = Bid.objects.last()
        self.assertEqual(response_post_bid.data.get('title'), bid_1.title)

        post_bid_data = {
            'title': "TestBid2"
        }
        response_post_bid = self.client.post(url_post_bid, post_bid_data)
        self.assertEqual(bet.bids.count(), 2)
        bid_2 = Bid.objects.last()
        self.assertEqual(response_post_bid.data.get('title'), bid_2.title)

        post_bid_data = {
            'title': "TestBid3"
        }
        response_post_bid = self.client.post(url_post_bid, post_bid_data)
        self.assertEqual(bet.bids.count(), 3)
        bid_3 = Bid.objects.last()
        self.assertEqual(response_post_bid.data.get('title'), bid_3.title)

        ####### Participating in first result with user 2
        self.login(2)

        url_post_bid_participant = reverse('bid-add-participant', args=(bid_1.id,))
        response_post_bid_participant = self.client.post(url_post_bid_participant)
        self.assertEqual(bid_1.participants.count(), 1)

        url_get_bid_participants = reverse('bid-participants', args=(bid_1.id,))
        response_get_bid_participants = self.client.get(url_get_bid_participants)
        self.assertEqual(len(response_get_bid_participants.data), 1)
        self.assertEqual(response_get_bid_participants.data[0]['username'], self.username_2)

        ####### Participating in second result with user 3
        self.login(3)

        url_post_bid_participant = reverse('bid-add-participant', args=(bid_2.id,))
        response_post_bid_participant = self.client.post(url_post_bid_participant)
        self.assertEqual(bid_2.participants.count(), 1)

        url_get_bid_participants = reverse('bid-participants', args=(bid_2.id,))
        response_get_bid_participants = self.client.get(url_get_bid_participants)
        self.assertEqual(len(response_get_bid_participants.data), 1)
        self.assertEqual(response_get_bid_participants.data[0]['username'], self.username_3)

        ####### Going to event state
        self.time_machine(16)
        bet.next_state()
        self.assertEqual(bet.bet_state, "event")

        ####### Going to resolving state
        self.time_machine(31)
        bet.next_state()
        self.assertEqual(bet.bet_state, "resolving")

        ###### Resolving bet with user 1 (resolving that result 1 is the winner)
        self.login(1)
        url_post_bet_resolve = reverse('bet-resolve', args=(bet.id,))
        post_resolve_data = {
            'claim_lottery_winner': bid_1.id,
            'claim_message': "ClaimMessageTest"
        }
        response_post_bet_resolve = self.client.post(url_post_bet_resolve, post_resolve_data)
        bet = Bet.objects.get(id=bet.id)
        self.assertEqual(bet.bet_state, "complaining")

        ###### Complaining bet with user 2 (complaining that nobody won)
        self.login(2)
        url_post_bet_complain = reverse('bid-complain', args=(bid_1.id,))
        post_complain_data = {
            'claim': 3,
            'claim_message': "ClaimComplainMessageTest"
        }
        response_post_bet_complain = self.client.post(url_post_bet_complain, post_complain_data)
        bet = Bet.objects.get(id=bet.id)
        self.assertEqual(bet.bet_state, "arbitrating")

        ###### Arbitrating bet with user 5 (arbitrating in favour of user 1, so result 1 is the actual winner)
        self.login(5)
        url_post_bet_arbitrate = reverse('bet-arbitrate', args=(bet.id,))
        post_arbitrate_data = {
            'claim_lottery_winner': bid_1.id,
            'claim_message': "ClaimArbitrateMessageTest"
        }
        response_post_bet_arbitrate = self.client.post(url_post_bet_arbitrate, post_arbitrate_data)
        bet = Bet.objects.get(id=bet.id)
        self.assertEqual(bet.bet_state, "closed")

        ####### User 5 should get the most points for arbitrating,
        ####### then user 2 for winning the lottery, then user 3 for participating
        ####### and finally user 1 with negative points for losing the conflict
        ranking = [self.username_5, self.username_1, self.username_3, self.username_2]
        real_ranking = [(p.user.username, p.points) for p in bet.points.all().order_by('-points')]
        self.assertEqual([p.user.username for p in bet.points.all().order_by('-points')], ranking)

        self.logout()

    '''
    def test_get_bet_list(self):
        pass

    def test_get_bet_detail(self):
        pass

    def test_create_bet(self):
        pass

    def test_update_bet(self):
        pass

    def test_update_bet_unauthorised(self):
        pass

    def test_delete_bet(self):
        pass

    def test_delete_bet_unauthorised(self):
        pass

    def test_accept_simple_bet(self):
        pass

    def test_resolve_simple_bet(self):
        pass

    def test_conflict_simple_bet(self):
        pass
    '''
