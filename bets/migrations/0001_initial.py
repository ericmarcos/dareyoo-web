# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):
    depends_on = (
        ('users', '0001_initial'),
    )

    def forwards(self, orm):
        # Adding model 'Bet'
        db.create_table(u'bets_bet', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('author', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='bets', null=True, to=orm['users.DareyooUser'])),
            ('title', self.gf('django.db.models.fields.CharField')(default='', max_length=255, null=True, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(default='', null=True, blank=True)),
            ('tags', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('amount', self.gf('django.db.models.fields.FloatField')(default=0, null=True, blank=True)),
            ('referee_escrow', self.gf('django.db.models.fields.FloatField')(default=0, null=True, blank=True)),
            ('bet_type', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=1, null=True, blank=True)),
            ('bet_state', self.gf('django_fsm.db.fields.fsmfield.FSMField')(default='bidding', max_length=50)),
            ('odds', self.gf('django.db.models.fields.FloatField')(default=0.5, null=True, blank=True)),
            ('accepted_bid', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='accepted', null=True, to=orm['bets.Bid'])),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True)),
            ('bidding_deadline', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('event_deadline', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('public', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('claim', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=None, null=True, blank=True)),
            ('claim_lottery_winner', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='winning_bet', null=True, to=orm['bets.Bid'])),
            ('claim_message', self.gf('django.db.models.fields.TextField')(default='', null=True, blank=True)),
            ('points', self.gf('django.db.models.fields.PositiveIntegerField')(default=0, null=True, blank=True)),
            ('referee', self.gf('django.db.models.fields.related.ForeignKey')(default=None, related_name='arbitrated_bets', null=True, blank=True, to=orm['users.DareyooUser'])),
            ('referee_claim', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=None, null=True, blank=True)),
            ('referee_lottery_winner', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='referee_winning_bet', null=True, to=orm['bets.Bid'])),
            ('log', self.gf('django.db.models.fields.TextField')(default='', null=True, blank=True)),
        ))
        db.send_create_signal(u'bets', ['Bet'])

        # Adding M2M table for field recipients on 'Bet'
        m2m_table_name = db.shorten_name(u'bets_bet_recipients')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('bet', models.ForeignKey(orm[u'bets.bet'], null=False)),
            ('dareyoouser', models.ForeignKey(orm[u'users.dareyoouser'], null=False))
        ))
        db.create_unique(m2m_table_name, ['bet_id', 'dareyoouser_id'])

        # Adding model 'Bid'
        db.create_table(u'bets_bid', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('author', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='bids', null=True, to=orm['users.DareyooUser'])),
            ('bet', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='bids', null=True, to=orm['bets.Bet'])),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('amount', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('referee_escrow', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True)),
            ('claim', self.gf('django.db.models.fields.PositiveSmallIntegerField')(max_length=63, null=True, blank=True)),
            ('claim_message', self.gf('django.db.models.fields.TextField')(default='', null=True, blank=True)),
            ('points', self.gf('django.db.models.fields.PositiveIntegerField')(default=0, null=True, blank=True)),
        ))
        db.send_create_signal(u'bets', ['Bid'])

        # Adding M2M table for field participants on 'Bid'
        m2m_table_name = db.shorten_name(u'bets_bid_participants')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('bid', models.ForeignKey(orm[u'bets.bid'], null=False)),
            ('dareyoouser', models.ForeignKey(orm[u'users.dareyoouser'], null=False))
        ))
        db.create_unique(m2m_table_name, ['bid_id', 'dareyoouser_id'])


    def backwards(self, orm):
        # Deleting model 'Bet'
        db.delete_table(u'bets_bet')

        # Removing M2M table for field recipients on 'Bet'
        db.delete_table(db.shorten_name(u'bets_bet_recipients'))

        # Deleting model 'Bid'
        db.delete_table(u'bets_bid')

        # Removing M2M table for field participants on 'Bid'
        db.delete_table(db.shorten_name(u'bets_bid_participants'))


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
            'author': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'bets'", 'null': 'True', 'to': u"orm['users.DareyooUser']"}),
            'bet_state': ('django_fsm.db.fields.fsmfield.FSMField', [], {'default': "'bidding'", 'max_length': '50'}),
            'bet_type': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1', 'null': 'True', 'blank': 'True'}),
            'bidding_deadline': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'claim': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'claim_lottery_winner': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'winning_bet'", 'null': 'True', 'to': u"orm['bets.Bid']"}),
            'claim_message': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True', 'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True', 'blank': 'True'}),
            'event_deadline': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'log': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True', 'blank': 'True'}),
            'odds': ('django.db.models.fields.FloatField', [], {'default': '0.5', 'null': 'True', 'blank': 'True'}),
            'points': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'recipients': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['users.DareyooUser']", 'null': 'True', 'blank': 'True'}),
            'referee': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'arbitrated_bets'", 'null': 'True', 'blank': 'True', 'to': u"orm['users.DareyooUser']"}),
            'referee_claim': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'referee_escrow': ('django.db.models.fields.FloatField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'referee_lottery_winner': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'referee_winning_bet'", 'null': 'True', 'to': u"orm['bets.Bid']"}),
            'tags': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'})
        },
        u'bets.bid': {
            'Meta': {'object_name': 'Bid'},
            'amount': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'author': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'bids'", 'null': 'True', 'to': u"orm['users.DareyooUser']"}),
            'bet': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'bids'", 'null': 'True', 'to': u"orm['bets.Bet']"}),
            'claim': ('django.db.models.fields.PositiveSmallIntegerField', [], {'max_length': '63', 'null': 'True', 'blank': 'True'}),
            'claim_message': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True', 'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'participants': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['users.DareyooUser']", 'null': 'True', 'blank': 'True'}),
            'points': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'referee_escrow': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'users.dareyoouser': {
            'Meta': {'object_name': 'DareyooUser'},
            'coins_available': ('django.db.models.fields.FloatField', [], {'default': '10', 'null': 'True', 'blank': 'True'}),
            'coins_locked': ('django.db.models.fields.FloatField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'date_of_birth': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '255', 'db_index': 'True'}),
            'facebook_uid': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'}),
            'following': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'followers'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['users.DareyooUser']"}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'points': ('django.db.models.fields.FloatField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'reference_user': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'invited_users'", 'null': 'True', 'to': u"orm['users.DareyooUser']"}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['bets']