# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding M2M table for field like_users on 'Discussion'
        m2m_table_name = db.shorten_name(u'odnoklassniki_discussions_discussion_like_users')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('discussion', models.ForeignKey(orm[u'odnoklassniki_discussions.discussion'], null=False)),
            ('user', models.ForeignKey(orm[u'odnoklassniki_users.user'], null=False))
        ))
        db.create_unique(m2m_table_name, ['discussion_id', 'user_id'])

        # Adding M2M table for field like_users on 'Comment'
        m2m_table_name = db.shorten_name(u'odnoklassniki_discussions_comment_like_users')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('comment', models.ForeignKey(orm[u'odnoklassniki_discussions.comment'], null=False)),
            ('user', models.ForeignKey(orm[u'odnoklassniki_users.user'], null=False))
        ))
        db.create_unique(m2m_table_name, ['comment_id', 'user_id'])

        # Adding field 'Discussion.like_users.through.time_from'
        db.add_column('odnoklassniki_discussions_discussion_like_users', 'time_from',
            self.gf('django.db.models.fields.DateTimeField')(null=True, db_index=True),
            keep_default=False)

        # Adding field 'Discussion.like_users.through.time_to'
        db.add_column('odnoklassniki_discussions_discussion_like_users', 'time_to',
            self.gf('django.db.models.fields.DateTimeField')(null=True, db_index=True),
            keep_default=False)

        # Adding field 'Comment.like_users.through.time_from'
        db.add_column('odnoklassniki_discussions_comment_like_users', 'time_from',
            self.gf('django.db.models.fields.DateTimeField')(null=True, db_index=True),
            keep_default=False)

        # Adding field 'Comment.like_users.through.time_to'
        db.add_column('odnoklassniki_discussions_comment_like_users', 'time_to',
            self.gf('django.db.models.fields.DateTimeField')(null=True, db_index=True),
            keep_default=False)

    def backwards(self, orm):
        # Removing M2M table for field like_users on 'Discussion'
        db.delete_table(db.shorten_name(u'odnoklassniki_discussions_discussion_like_users'))

        # Removing M2M table for field like_users on 'Comment'
        db.delete_table(db.shorten_name(u'odnoklassniki_discussions_comment_like_users'))


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
            'like_users': ('m2m_history.fields.ManyToManyHistoryField', [], {'related_name': "'like_comments'", 'symmetrical': 'False', 'to': u"orm['odnoklassniki_users.User']"}),
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
            'like_users': ('m2m_history.fields.ManyToManyHistoryField', [], {'related_name': "'like_discussions'", 'symmetrical': 'False', 'to': u"orm['odnoklassniki_users.User']"}),
            'liked_it': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'likes_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'message': ('django.db.models.fields.TextField', [], {}),
            'new_comments_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'object_type': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'owner_content_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'odnoklassniki_discussions_owners'", 'to': u"orm['contenttypes.ContentType']"}),
            'owner_id': ('django.db.models.fields.BigIntegerField', [], {'db_index': 'True'}),
            'ref_objects': ('annoying.fields.JSONField', [], {'null': 'True'}),
            'title': ('django.db.models.fields.TextField', [], {})
        },
        u'odnoklassniki_users.user': {
            'Meta': {'object_name': 'User'},
            'allows_anonym_access': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'birthday': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'city': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'country': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'country_code': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'current_status': ('django.db.models.fields.TextField', [], {}),
            'current_status_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'current_status_id': ('django.db.models.fields.BigIntegerField', [], {'null': 'True'}),
            'fetched': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'gender': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True'}),
            'has_email': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'has_service_invisible': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.BigIntegerField', [], {'primary_key': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'last_online': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'locale': ('django.db.models.fields.CharField', [], {'max_length': '5'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'photo_id': ('django.db.models.fields.BigIntegerField', [], {'null': 'True'}),
            'pic1024x768': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'pic128max': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'pic128x128': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'pic180min': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'pic190x190': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'pic240min': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'pic320min': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'pic50x50': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'pic640x480': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'private': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'registered_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'shortname': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True'}),
            'url_profile': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'url_profile_mobile': ('django.db.models.fields.URLField', [], {'max_length': '200'})
        }
    }

    complete_apps = ['odnoklassniki_discussions']