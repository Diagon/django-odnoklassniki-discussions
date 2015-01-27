# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'Discussion.type'
        db.delete_column(u'odnoklassniki_discussions_discussion', 'type')

        # Adding field 'Discussion.object_type'
        db.add_column(u'odnoklassniki_discussions_discussion', 'object_type',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=20),
                      keep_default=False)

        # Deleting field 'Comment.type'
        db.delete_column(u'odnoklassniki_discussions_comment', 'type')

        # Adding field 'Comment.object_type'
        db.add_column(u'odnoklassniki_discussions_comment', 'object_type',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=20),
                      keep_default=False)


    def backwards(self, orm):
        # Adding field 'Discussion.type'
        db.add_column(u'odnoklassniki_discussions_discussion', 'type',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=20),
                      keep_default=False)

        # Deleting field 'Discussion.object_type'
        db.delete_column(u'odnoklassniki_discussions_discussion', 'object_type')

        # Adding field 'Comment.type'
        db.add_column(u'odnoklassniki_discussions_comment', 'type',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=20),
                      keep_default=False)

        # Deleting field 'Comment.object_type'
        db.delete_column(u'odnoklassniki_discussions_comment', 'object_type')


    models = {
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'odnoklassniki_discussions.comment': {
            'Meta': {'object_name': 'Comment'},
            'attrs': ('annoying.fields.JSONField', [], {'null': 'True'}),
            'author_content_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'odnoklassniki_comments_authors'", 'to': u"orm['contenttypes.ContentType']"}),
            'author_id': ('django.db.models.fields.BigIntegerField', [], {'db_index': 'True'}),
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            'discussion': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'comments'", 'to': u"orm['odnoklassniki_discussions.Discussion']"}),
            'fetched': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.CharField', [], {'max_length': '68', 'primary_key': 'True'}),
            'liked_it': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'likes_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'object_type': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'owner_content_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'odnoklassniki_comments_owners'", 'to': u"orm['contenttypes.ContentType']"}),
            'owner_id': ('django.db.models.fields.BigIntegerField', [], {'db_index': 'True'}),
            'reply_to_author_content_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'odnoklassniki_comments_reply_to_authors'", 'null': 'True', 'to': u"orm['contenttypes.ContentType']"}),
            'reply_to_author_id': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'db_index': 'True'}),
            'reply_to_comment': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['odnoklassniki_discussions.Comment']", 'null': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {})
        },
        u'odnoklassniki_discussions.discussion': {
            'Meta': {'object_name': 'Discussion'},
            'attrs': ('annoying.fields.JSONField', [], {'null': 'True'}),
            'author_content_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'odnoklassniki_discussions_authors'", 'to': u"orm['contenttypes.ContentType']"}),
            'author_id': ('django.db.models.fields.BigIntegerField', [], {'db_index': 'True'}),
            'comments_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            'entities': ('annoying.fields.JSONField', [], {'null': 'True'}),
            'fetched': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.BigIntegerField', [], {'primary_key': 'True'}),
            'last_activity_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'last_user_access_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'liked_it': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'likes_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'message': ('django.db.models.fields.TextField', [], {}),
            'new_comments_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'object_type': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'owner_content_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'odnoklassniki_discussions_owners'", 'to': u"orm['contenttypes.ContentType']"}),
            'owner_id': ('django.db.models.fields.BigIntegerField', [], {'db_index': 'True'}),
            'ref_objects': ('annoying.fields.JSONField', [], {'null': 'True'}),
            'title': ('django.db.models.fields.TextField', [], {})
        }
    }

    complete_apps = ['odnoklassniki_discussions']