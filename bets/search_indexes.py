from django.utils.timezone import now
from haystack import indexes
from bets.models import Bet


class BetIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    author = indexes.CharField(model_attr='user')
    created_at = indexes.DateTimeField(model_attr='created_at')
    bidding_deadline = indexes.DateTimeField(model_attr='bidding_deadline')
    bet_state = indexes.CharField(model_attr='bet_state')
    public = indexes.BooleanField(model_attr='public')

    def get_model(self):
        return Bet

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.filter(created_at__lte=now())