# -*- coding: utf-8 -*-
from django.db import models
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.utils.translation import ugettext as _
from django.core.exceptions import ImproperlyConfigured
from odnoklassniki_api.models import OdnoklassnikiManager, OdnoklassnikiPKModel, OdnoklassnikiModel
from odnoklassniki_api.fields import JSONField
from odnoklassniki_groups.models import Group
from odnoklassniki_users.models import User
from odnoklassniki_api.decorators import fetch_all, atomic
from m2m_history.fields import ManyToManyHistoryField
import logging
import re

log = logging.getLogger('odnoklassniki_discussions')

DISCUSSION_TYPES = [
    'GROUP_TOPIC',
    'GROUP_PHOTO',
    'USER_STATUS',
    'USER_PHOTO',
    'USER_FORUM',
    'USER_ALBUM',
    'USER_2LVL_FORUM',
    'MOVIE',
    'SCHOOL_FORUM',
    'HAPPENING_TOPIC',
    'GROUP_MOVIE',
    'CITY_NEWS',
    'CHAT',
]
COMMENT_TYPES = ['ACTIVE_MESSAGE']

DISCUSSION_TYPE_CHOICES = [(type, type) for type in DISCUSSION_TYPES]
COMMENT_TYPE_CHOICES = [(type, type) for type in COMMENT_TYPES]

class DiscussionRemoteManager(OdnoklassnikiManager):

    def fetch(self, **kwargs):
        if 'id' in kwargs and 'type' in kwargs:
            return self.fetch_one(**kwargs)
        elif 'group' in kwargs:
            return self.fetch_for_group(**kwargs)
        else:
            raise Exception("Wrong atributes for Discussion.remote.fetch() method kwargs=%s" % kwargs)

    @atomic
    def fetch_one(self, id, type, **kwargs):
        if type not in DISCUSSION_TYPES:
            raise ValueError("Wrong value of type argument %s" % type)

        kwargs['discussionId'] = id
        kwargs['discussionType'] = type
        # with `fields` response doesn't contain `entities` field
        #kwargs['fields'] = self.get_request_fields('discussion')
        return super(DiscussionRemoteManager, self).fetch(method='get_one', **kwargs)

    def update_discussions_count(self, instances, group, *args, **kwargs):
        group.discussions_count = len(instances)
        group.save()
        return instances

    @atomic
    @fetch_all(return_all=update_discussions_count)
    def fetch_for_group(self, group, count=100, **kwargs):
        kwargs['gid'] = group.pk
        kwargs['count'] = int(count)
        kwargs['patterns'] = 'POST'
        kwargs['fields'] = self.get_request_fields('feed', 'media_topic', prefix=True)

        response = super(DiscussionRemoteManager, self).api_call(method='stream', **kwargs)
        # has_more not in dict and we need to handle pagination manualy
        if 'feeds' not in response:
            response.pop('anchor', None)
            discussions = self.model.objects.none()
        else:
            feed = [feed for feed in response['feeds'] if feed['pattern'] == 'POST']
            discussions = self.parse_response(feed, {'owner_id': group.pk, 'owner_content_type_id': ContentType.objects.get_for_model(Group).pk})
            discussions = self.get_or_create_from_instances_list(discussions)

        return discussions, response


class CommentRemoteManager(OdnoklassnikiManager):

    @fetch_all
    def get(self, discussion, count=100, **kwargs):
        kwargs['discussionId'] = discussion.pk
        kwargs['discussionType'] = discussion.object_type
        kwargs['count'] = int(count)

        response = super(CommentRemoteManager, self).api_call(**kwargs)
        comments = self.parse_response(response['comments'], {'discussion_id': discussion.pk})

        return comments, response

    @atomic
    def fetch(self, discussion, **kwargs):
        '''
        Get all comments, reverse order and save them, because we need to store reply_to_comment relation
        '''
        comments = self.get(discussion=discussion, **kwargs)
        comments.reverse()
        comments = self.get_or_create_from_instances_list(comments)

        discussion.comments_count = comments.count()
        discussion.save()

        return comments


class Discussion(OdnoklassnikiPKModel):
    class Meta:
        verbose_name = _('Odnoklassniki discussion')
        verbose_name_plural = _('Odnoklassniki discussions')

    methods_namespace = ''
    remote_pk_field = 'object_id'

    owner_content_type = models.ForeignKey(ContentType, related_name='odnoklassniki_discussions_owners')
    owner_id = models.BigIntegerField(db_index=True)
    owner = generic.GenericForeignKey('owner_content_type', 'owner_id')

    author_content_type = models.ForeignKey(ContentType, related_name='odnoklassniki_discussions_authors')
    author_id = models.BigIntegerField(db_index=True)
    author = generic.GenericForeignKey('author_content_type', 'author_id')

    object_type = models.CharField(max_length=20, choices=DISCUSSION_TYPE_CHOICES)
    title = models.TextField()
    message = models.TextField()

    date = models.DateTimeField()
    last_activity_date = models.DateTimeField(null=True)
    last_user_access_date = models.DateTimeField(null=True)

    new_comments_count = models.PositiveIntegerField(default=0)
    comments_count = models.PositiveIntegerField(default=0)
    likes_count = models.PositiveIntegerField(default=0)

    liked_it = models.BooleanField()

    entities = JSONField(null=True)
    ref_objects = JSONField(null=True)
    attrs = JSONField(null=True)

    like_users = ManyToManyHistoryField(User, related_name='like_discussions')

    remote = DiscussionRemoteManager(methods={
        'get': 'discussions.getList',
        'get_one': 'discussions.get',
        'get_likes': 'discussions.getDiscussionLikes',
        'stream': 'stream.get',
    })

#     def __unicode__(self):
#         return self.name

    @property
    def refresh_kwargs(self):
        return {'id': self.pk, 'type': self.object_type or 'GROUP_TOPIC'}

    @property
    def slug(self):
        return '%s/topic/%s' % (self.owner.slug, self.id)

    def parse(self, response):
        if 'discussion' in response:
            response.update(response.pop('discussion'))

        # in API owner is author
        if 'owner_uid' in response:
             response['author_id'] = response.pop('owner_uid')

        # some name cleaning
        if 'like_count' in response:
            response['likes_count'] = response.pop('like_count')

        if 'total_comments_count' in response:
            response['comments_count'] = response.pop('total_comments_count')

        if 'creation_date' in response:
            response['date'] = response.pop('creation_date')

        # response of stream.get has another format
        if '{media_topic' in response['message']:
            regexp = r'{media_topic:?(\d+)?}'
            m = re.findall(regexp, response['message'])
            if len(m):
                response['id'] = m[0]
                response['message'] = re.sub(regexp, '', response['message'])

        return super(Discussion, self).parse(response)

    def save(self, *args, **kwargs):

        # make 2 dicts {id: instance} for group and users from entities
        if self.entities:
            entities = {
                'users': [],
                'groups': [],
            }
            for resource in self.entities.get('users', []):
                entities['users'] += [User.remote.get_or_create_from_resource(resource)]
            for resource in self.entities.get('groups', []):
                entities['groups'] += [Group.remote.get_or_create_from_resource(resource)]
            for field in ['users','groups']:
                entities[field] = dict([(instance.id, instance) for instance in entities[field]])

            # set owner
            for resource in self.ref_objects:
                id = int(resource['id'])
                if resource['type'] == 'GROUP':
                    self.owner = entities['groups'][id]
                elif resource['type'] == 'USER':
                    self.owner = entities['user'][id]
                else:
                    log.warning("Strange type of object in ref_objects %s for duscussion ID=%s" % (resource, self.id))

            # set author
            if self.author_id:
                if self.author_id in entities['groups']:
                    self.author = entities['groups'][self.author_id]
                elif self.author_id in entities['users']:
                    self.author = entities['users'][self.author_id]
                else:
                    log.warning("Imposible to find author with ID=%s in entities of duscussion ID=%s" % (self.author_id, self.id))
                    self.author_id = None

        if self.owner and not self.author_id:
            # of no author_id (owner_uid), so it's equal to owner from ref_objects
            self.author = self.owner

        return super(Discussion, self).save(*args, **kwargs)

    def fetch_comments(self, **kwargs):
        return Comment.remote.fetch(discussion=self, **kwargs)

    def update_likes_count(self, instances, *args, **kwargs):
        users = User.objects.filter(pk__in=instances)
        self.like_users = users
        self.likes_count = len(instances)
        self.save()
        return users

    @atomic
    @fetch_all(return_all=update_likes_count)
    def fetch_likes(self, count=100, **kwargs):
        kwargs['discussionId'] = self.pk
        kwargs['discussionType'] = self.object_type
        kwargs['count'] = int(count)
#        kwargs['fields'] = Discussion.remote.get_request_fields('user')

        response = Discussion.remote.api_call(method='get_likes', **kwargs)
        # has_more not in dict and we need to handle pagination manualy
        if 'users' not in response:
            response.pop('anchor', None)
            users_ids = []
        else:
            users_ids = list(User.remote.get_or_create_from_resources_list(response['users']).values_list('pk', flat=True))

        return users_ids, response


class Comment(OdnoklassnikiModel):
    class Meta:
        verbose_name = _('Odnoklassniki comment')
        verbose_name_plural = _('Odnoklassniki comments')

    methods_namespace = 'discussions'

    # temporary variable for distance from parse() to save()
    author_type = None

    id = models.CharField(max_length=68, primary_key=True)

    discussion = models.ForeignKey(Discussion, related_name='comments')

    # denormalization for query optimization
    owner_content_type = models.ForeignKey(ContentType, related_name='odnoklassniki_comments_owners')
    owner_id = models.BigIntegerField(db_index=True)
    owner = generic.GenericForeignKey('owner_content_type', 'owner_id')

    author_content_type = models.ForeignKey(ContentType, related_name='odnoklassniki_comments_authors')
    author_id = models.BigIntegerField(db_index=True)
    author = generic.GenericForeignKey('author_content_type', 'author_id')

    reply_to_comment = models.ForeignKey('self', null=True, verbose_name=u'Это ответ на комментарий')

    reply_to_author_content_type = models.ForeignKey(ContentType, null=True, related_name='odnoklassniki_comments_reply_to_authors')
    reply_to_author_id = models.BigIntegerField(db_index=True, null=True)
    reply_to_author = generic.GenericForeignKey('reply_to_author_content_type', 'reply_to_author_id')

    object_type = models.CharField(max_length=20, choices=COMMENT_TYPE_CHOICES)
    text = models.TextField()

    date = models.DateTimeField()

    likes_count = models.PositiveIntegerField(default=0)
    liked_it = models.BooleanField()

    attrs = JSONField(null=True)

    like_users = ManyToManyHistoryField(User, related_name='like_comments')

    remote = CommentRemoteManager(methods={
        'get': 'getComments',
        'get_one': 'getComment',
        'get_likes': 'getCommentLikes',
    })

    def parse(self, response):
        # rename becouse discussion has object_type
        if 'type' in response:
            response['object_type'] = response.pop('type')

        if 'like_count' in response:
            response['likes_count'] = response.pop('like_count')
        if 'reply_to_id' in response:
            response['reply_to_author_id'] = response.pop('reply_to_id')
        if 'reply_to_comment_id' in response:
            response['reply_to_comment'] = response.pop('reply_to_comment_id')

        # if author is a group
        if 'author_type' in response:
            response.pop('author_name')
            self.author_type = response.pop('author_type')

        return super(Comment, self).parse(response)

    def save(self, *args, **kwargs):
        self.owner = self.discussion.owner

        if self.author_id:
            if self.author_type == 'GROUP':
                if self.author_id == self.owner_id:
                    self.author = self.owner
                else:
                    self.author = Group.remote.fetch(ids=[self.author_id])[0]
            else:
                try:
                    self.author = User.objects.get(pk=self.author_id)
                except User.DoesNotExist:
                    self.author = User.remote.fetch(ids=[self.author_id])[0]

        # it's hard to get proper reply_to_author_content_type in case we fetch comments from last
        if self.reply_to_author_id and not self.reply_to_author_content_type:
             self.reply_to_author_content_type = ContentType.objects.get_for_model(User)
#         if self.reply_to_comment_id and self.reply_to_author_id and not self.reply_to_author_content_type:
#             try:
#                 self.reply_to_author = User.objects.get(pk=self.reply_to_author_id)
#             except User.DoesNotExist:
#                 self.reply_to_author = self.reply_to_comment.author

        # check for existing comment from self.reply_to_comment to prevent ItegrityError
        if self.reply_to_comment_id:
            try:
                self.reply_to_comment = Comment.objects.get(pk=self.reply_to_comment_id)
            except Comment.DoesNotExist:
                log.error("Try to save comment ID=%s with reply_to_comment_id=%s that doesn't exist in DB" % (self.pk, self.reply_to_comment_id))
                self.reply_to_comment = None

        return super(Comment, self).save(*args, **kwargs)

    def update_likes_count(self, instances, *args, **kwargs):
        users = User.objects.filter(pk__in=instances)
        self.like_users = users
        self.likes_count = len(instances)
        self.save()
        return users

    @atomic
    @fetch_all(return_all=update_likes_count)
    def fetch_likes(self, count=100, **kwargs):
        kwargs['comment_id'] = self.pk
        kwargs['discussionId'] = self.discussion.pk
        kwargs['discussionType'] = self.discussion.object_type
        kwargs['count'] = int(count)
#        kwargs['fields'] = Comment.remote.get_request_fields('user')

        response = Comment.remote.api_call(method='get_likes', **kwargs)
        # has_more not in dict and we need to handle pagination manualy
        if 'users' not in response:
            response.pop('anchor', None)
            users_ids = []
        else:
            users_ids = list(User.remote.get_or_create_from_resources_list(response['users']).values_list('pk', flat=True))

        return users_ids, response
