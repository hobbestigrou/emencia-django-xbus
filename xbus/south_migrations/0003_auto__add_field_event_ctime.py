# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Event.ctime'
        db.add_column(u'xbus_event', 'ctime',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Event.ctime'
        db.delete_column(u'xbus_event', 'ctime')


    models = {
        u'xbus.event': {
            'Meta': {'object_name': 'Event'},
            'ctime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'direction': ('django.db.models.fields.CharField', [], {'max_length': '5'}),
            'event_type': ('django.db.models.fields.CharField', [], {'max_length': '80'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item': ('django.db.models.fields.BinaryField', [], {}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'xbus_message_correlation_id': ('django.db.models.fields.CharField', [], {'max_length': '36'}),
            'xref': ('django.db.models.fields.CharField', [], {'max_length': '36'})
        }
    }

    complete_apps = ['xbus']