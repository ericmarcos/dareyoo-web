# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Conversation'
        db.create_table(u'wabots_conversation', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('jid', self.gf('django.db.models.fields.CharField')(default='', max_length=255, null=True, blank=True)),
            ('provider', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=1, null=True, blank=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True)),
            ('last_interaction', self.gf('django.db.models.fields.DateTimeField')(default=None, null=True, blank=True)),
            ('messages_log', self.gf('django.db.models.fields.TextField')(default='', null=True, blank=True)),
            ('autoresponse', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal(u'wabots', ['Conversation'])

        # Adding M2M table for field users on 'Conversation'
        m2m_table_name = db.shorten_name(u'wabots_conversation_users')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('conversation', models.ForeignKey(orm[u'wabots.conversation'], null=False)),
            ('dareyoouser', models.ForeignKey(orm[u'users.dareyoouser'], null=False))
        ))
        db.create_unique(m2m_table_name, ['conversation_id', 'dareyoouser_id'])

        # Adding model 'BaseBotInstance'
        db.create_table(u'wabots_basebotinstance', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('polymorphic_ctype', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'polymorphic_wabots.basebotinstance_set', null=True, to=orm['contenttypes.ContentType'])),
            ('conversation', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='bots', null=True, to=orm['wabots.Conversation'])),
            ('category', self.gf('django.db.models.fields.CharField')(default=None, max_length=255, null=True, blank=True)),
            ('silent', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('priority', self.gf('django.db.models.fields.SmallIntegerField')(default=0)),
            ('clients', self.gf('django.db.models.fields.CharField')(default='', max_length=255, null=True, blank=True)),
        ))
        db.send_create_signal(u'wabots', ['BaseBotInstance'])

        # Adding model 'PingPongBot'
        db.create_table(u'wabots_pingpongbot', (
            (u'basebotinstance_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['wabots.BaseBotInstance'], unique=True, primary_key=True)),
        ))
        db.send_create_signal(u'wabots', ['PingPongBot'])

        # Adding model 'AliceBot'
        db.create_table(u'wabots_alicebot', (
            (u'basebotinstance_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['wabots.BaseBotInstance'], unique=True, primary_key=True)),
            ('brain_file', self.gf('django.db.models.fields.files.FileField')(max_length=100, null=True, blank=True)),
            ('session', self.gf('jsonfield.fields.JSONField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'wabots', ['AliceBot'])


    def backwards(self, orm):
        # Deleting model 'Conversation'
        db.delete_table(u'wabots_conversation')

        # Removing M2M table for field users on 'Conversation'
        db.delete_table(db.shorten_name(u'wabots_conversation_users'))

        # Deleting model 'BaseBotInstance'
        db.delete_table(u'wabots_basebotinstance')

        # Deleting model 'PingPongBot'
        db.delete_table(u'wabots_pingpongbot')

        # Deleting model 'AliceBot'
        db.delete_table(u'wabots_alicebot')


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
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
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
            'username': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'}),
            'whatsapp_jid': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'whatsapp_verification_code': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'whatsapp_verified': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        u'wabots.alicebot': {
            'Meta': {'ordering': "['priority']", 'object_name': 'AliceBot', '_ormbases': [u'wabots.BaseBotInstance']},
            u'basebotinstance_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['wabots.BaseBotInstance']", 'unique': 'True', 'primary_key': 'True'}),
            'brain_file': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'session': ('jsonfield.fields.JSONField', [], {'null': 'True', 'blank': 'True'})
        },
        u'wabots.basebotinstance': {
            'Meta': {'ordering': "['priority']", 'object_name': 'BaseBotInstance'},
            'category': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'clients': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'conversation': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'bots'", 'null': 'True', 'to': u"orm['wabots.Conversation']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'polymorphic_ctype': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'polymorphic_wabots.basebotinstance_set'", 'null': 'True', 'to': u"orm['contenttypes.ContentType']"}),
            'priority': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
            'silent': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        u'wabots.conversation': {
            'Meta': {'object_name': 'Conversation'},
            'autoresponse': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'jid': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'last_interaction': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'messages_log': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True', 'blank': 'True'}),
            'provider': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1', 'null': 'True', 'blank': 'True'}),
            'users': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'conversations'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['users.DareyooUser']"})
        },
        u'wabots.pingpongbot': {
            'Meta': {'ordering': "['priority']", 'object_name': 'PingPongBot', '_ormbases': [u'wabots.BaseBotInstance']},
            u'basebotinstance_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['wabots.BaseBotInstance']", 'unique': 'True', 'primary_key': 'True'})
        }
    }

    complete_apps = ['wabots']