# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Tournament'
        db.create_table(u'gamification_tournament', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('author', self.gf('django.db.models.fields.related.OneToOneField')(blank=True, related_name='tournaments_created', unique=True, null=True, to=orm['users.DareyooUser'])),
            ('public', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('only_author', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('tag', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('start', self.gf('django.db.models.fields.DateTimeField')(default=None, null=True, blank=True)),
            ('end', self.gf('django.db.models.fields.DateTimeField')(default=None, null=True, blank=True)),
            ('pic', self.gf('django.db.models.fields.files.ImageField')(max_length=100, null=True, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(default='', null=True, blank=True)),
        ))
        db.send_create_signal(u'gamification', ['Tournament'])

        # Adding M2M table for field participants on 'Tournament'
        m2m_table_name = db.shorten_name(u'gamification_tournament_participants')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('tournament', models.ForeignKey(orm[u'gamification.tournament'], null=False)),
            ('dareyoouser', models.ForeignKey(orm[u'users.dareyoouser'], null=False))
        ))
        db.create_unique(m2m_table_name, ['tournament_id', 'dareyoouser_id'])

        # Adding M2M table for field bets on 'Tournament'
        m2m_table_name = db.shorten_name(u'gamification_tournament_bets')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('tournament', models.ForeignKey(orm[u'gamification.tournament'], null=False)),
            ('bet', models.ForeignKey(orm[u'bets.bet'], null=False))
        ))
        db.create_unique(m2m_table_name, ['tournament_id', 'bet_id'])

        # Adding field 'UserBadges.precal_total_wins'
        db.add_column(u'gamification_userbadges', 'precal_total_wins',
                      self.gf('django.db.models.fields.IntegerField')(default=0, null=True, blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting model 'Tournament'
        db.delete_table(u'gamification_tournament')

        # Removing M2M table for field participants on 'Tournament'
        db.delete_table(db.shorten_name(u'gamification_tournament_participants'))

        # Removing M2M table for field bets on 'Tournament'
        db.delete_table(db.shorten_name(u'gamification_tournament_bets'))

        # Deleting field 'UserBadges.precal_total_wins'
        db.delete_column(u'gamification_userbadges', 'precal_total_wins')


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
            'finished_at': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'log': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True', 'blank': 'True'}),
            'odds': ('django.db.models.fields.FloatField', [], {'default': '2', 'null': 'True', 'blank': 'True'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'recipients': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['users.DareyooUser']", 'null': 'True', 'blank': 'True'}),
            'referee': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'arbitrated_bets'", 'null': 'True', 'blank': 'True', 'to': u"orm['users.DareyooUser']"}),
            'referee_claim': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'referee_escrow': ('django.db.models.fields.FloatField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'referee_lottery_winner': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'referee_winning_bet'", 'null': 'True', 'to': u"orm['bets.Bid']"}),
            'referee_message': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True', 'blank': 'True'}),
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
            'participants': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['users.DareyooUser']", 'null': 'True', 'blank': 'True'}),
            'points': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'gamification.tournament': {
            'Meta': {'object_name': 'Tournament'},
            'author': ('django.db.models.fields.related.OneToOneField', [], {'blank': 'True', 'related_name': "'tournaments_created'", 'unique': 'True', 'null': 'True', 'to': u"orm['users.DareyooUser']"}),
            'bets': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'tournaments'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['bets.Bet']"}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True', 'blank': 'True'}),
            'end': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'only_author': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'participants': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'tournaments'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['users.DareyooUser']"}),
            'pic': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'start': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'tag': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'})
        },
        u'gamification.userbadges': {
            'Meta': {'object_name': 'UserBadges'},
            'fair_play': ('django.db.models.fields.SmallIntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'loser': ('django.db.models.fields.SmallIntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'max_coins': ('django.db.models.fields.SmallIntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'precal_total_wins': ('django.db.models.fields.IntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'straight_wins': ('django.db.models.fields.SmallIntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'total_wins': ('django.db.models.fields.SmallIntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'blank': 'True', 'related_name': "'badges'", 'unique': 'True', 'null': 'True', 'to': u"orm['users.DareyooUser']"}),
            'week_points': ('django.db.models.fields.SmallIntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'})
        },
        u'gamification.userpoints': {
            'Meta': {'object_name': 'UserPoints'},
            'bet': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'points'", 'null': 'True', 'to': u"orm['bets.Bet']"}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'points': ('django.db.models.fields.FloatField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'points'", 'null': 'True', 'to': u"orm['users.DareyooUser']"})
        },
        u'users.dareyoouser': {
            'Meta': {'object_name': 'DareyooUser'},
            'coins_available': ('django.db.models.fields.FloatField', [], {'default': '10', 'null': 'True', 'blank': 'True'}),
            'coins_locked': ('django.db.models.fields.FloatField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '255', 'db_index': 'True'}),
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
            'reference_user': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'invited_users'", 'null': 'True', 'to': u"orm['users.DareyooUser']"}),
            'registered': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['gamification']