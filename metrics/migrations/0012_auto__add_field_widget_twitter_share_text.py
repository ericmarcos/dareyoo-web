# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Widget.twitter_share_text'
        db.add_column(u'metrics_widget', 'twitter_share_text',
                      self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Widget.twitter_share_text'
        db.delete_column(u'metrics_widget', 'twitter_share_text')


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'bets.bet': {
            'Meta': {'object_name': 'Bet'},
            'accepted_bid': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'accepted'", 'null': 'True', 'to': u"orm['bets.Bid']"}),
            'amount': ('django.db.models.fields.FloatField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'arbitrated_at': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'author': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'bets'", 'null': 'True', 'to': u"orm['users.DareyooUser']"}),
            'bet_state': ('django_fsm.db.fields.fsmfield.FSMField', [], {'default': "'bidding'", 'max_length': '50'}),
            'bet_type': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1', 'null': 'True', 'blank': 'True'}),
            'bidding_deadline': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'claim': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'claim_lottery_winner': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'winning_bet'", 'null': 'True', 'to': u"orm['bets.Bid']"}),
            'claim_message': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True', 'blank': 'True'}),
            'complained_at': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True', 'blank': 'True'}),
            'event_deadline': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'finished_at': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'log': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True', 'blank': 'True'}),
            'lottery_type': ('django.db.models.fields.CharField', [], {'default': "'generic'", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'odds': ('django.db.models.fields.FloatField', [], {'default': '2', 'null': 'True', 'blank': 'True'}),
            'open_lottery': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'recipients': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['users.DareyooUser']", 'null': 'True', 'blank': 'True'}),
            'referee': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'arbitrated_bets'", 'null': 'True', 'blank': 'True', 'to': u"orm['users.DareyooUser']"}),
            'referee_claim': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'referee_escrow': ('django.db.models.fields.FloatField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'referee_lottery_winner': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'referee_winning_bet'", 'null': 'True', 'to': u"orm['bets.Bid']"}),
            'referee_message': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True', 'blank': 'True'}),
            'resolved_at': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'tags': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'})
        },
        u'bets.bid': {
            'Meta': {'object_name': 'Bid'},
            'amount': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'author': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'bids'", 'null': 'True', 'to': u"orm['users.DareyooUser']"}),
            'bet': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'bids'", 'null': 'True', 'to': u"orm['bets.Bet']"}),
            'claim': ('django.db.models.fields.PositiveSmallIntegerField', [], {'max_length': '63', 'null': 'True', 'blank': 'True'}),
            'claim_author': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'lottery_claimer'", 'null': 'True', 'to': u"orm['users.DareyooUser']"}),
            'claim_message': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True', 'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'participants': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'participated_bids'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['users.DareyooUser']"}),
            'pic': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'metrics.useractivation': {
            'Meta': {'object_name': 'UserActivation'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'level': ('django.db.models.fields.IntegerField', [], {'default': '1', 'null': 'True', 'blank': 'True'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'activations'", 'null': 'True', 'to': u"orm['users.DareyooUser']"})
        },
        u'metrics.widget': {
            'Meta': {'object_name': 'Widget'},
            'bets': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'widgets'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['bets.Bet']"}),
            'bg_pic': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'footer_link': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'footer_pic': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'header_link': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'header_pic': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'next_bets': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'widgets_next'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['bets.Bet']"}),
            'twitter_share_text': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'})
        },
        u'metrics.widgetactivation': {
            'Meta': {'object_name': 'WidgetActivation'},
            'banner_clicked': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'bet': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'widget_activations'", 'null': 'True', 'to': u"orm['bets.Bet']"}),
            'from_host': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'from_ip': ('django.db.models.fields.GenericIPAddressField', [], {'max_length': '39', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'level': ('django.db.models.fields.IntegerField', [], {'default': '1', 'null': 'True', 'blank': 'True'}),
            'medium_shared': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'participate_result': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'widget': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'activations'", 'null': 'True', 'to': u"orm['metrics.Widget']"})
        },
        u'users.dareyoouser': {
            'Meta': {'object_name': 'DareyooUser'},
            'coins_available': ('django.db.models.fields.FloatField', [], {'default': '100', 'null': 'True', 'blank': 'True'}),
            'coins_locked': ('django.db.models.fields.FloatField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '255', 'db_index': 'True'}),
            'email_notifications': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'following': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'followers'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['users.DareyooUser']"}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_pro': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_vip': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'profile_pic': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'reference_campaign': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'reference_user': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'invited_users'", 'null': 'True', 'to': u"orm['users.DareyooUser']"}),
            'registered': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['metrics']