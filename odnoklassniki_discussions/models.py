# -*- coding: utf-8 -*-
import logging
import re

from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.utils.translation import ugettext as _
from m2m_history.fields import ManyToManyHistoryField
from odnoklassniki_api.decorators import atomic, fetch_all
from odnoklassniki_api.fields import JSONField
from odnoklassniki_api.models import (OdnoklassnikiModel, OdnoklassnikiPKModel,
                                      OdnoklassnikiTimelineManager)
from odnoklassniki_users.models import User

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
DISCUSSION_TYPE_DEFAULT = 'GROUP_TOPIC'


class DiscussionRemoteManager(OdnoklassnikiTimelineManager):

    @atomic
    def fetch_one(self, id, type, **kwargs):
        if type not in DISCUSSION_TYPES:
            raise ValueError("Wrong value of type argument %s" % type)

        kwargs['discussionId'] = id
        kwargs['discussionType'] = type
        # with `fields` response doesn't contain `entities` field
        kwargs['fields'] = self.get_request_fields('discussions', 'media_topic', 'group', 'user', prefix=True)

        result = super(OdnoklassnikiTimelineManager, self).get(method='get_one', **kwargs)
        return self.get_or_create_from_instance(result)

    @fetch_all
    def get(self, **kwargs):
        return super(DiscussionRemoteManager, self).get(**kwargs), self.response

    def parse_response(self, response, extra_fields=None):
        if 'media_topics' in response:
            response = response['media_topics']
        elif 'owner_id' in extra_fields:
            # in case of fetch_group
            # TODO: change condition based on response
            # has_more not in dict and we need to handle pagination manualy
            if 'feeds' not in response:
                response.pop('anchor', None)
                return self.model.objects.none()
            else:
                response = [feed for feed in response['feeds'] if feed['pattern'] == 'POST']
        else:
            # in case of fetch_one
            pass

        return super(DiscussionRemoteManager, self).parse_response(response, extra_fields)

#     def update_discussions_count(self, instances, group, *args, **kwargs):
#         group.discussions_count = len(instances)
#         group.save()
#         return instances

    @atomic
    @fetch_all(has_more=None)
    def fetch_group(self, group, count=100, **kwargs):
        from odnoklassniki_groups.models import Group

        kwargs['gid'] = group.pk
        kwargs['count'] = int(count)
        kwargs['patterns'] = 'POST'
        kwargs['fields'] = self.get_request_fields('feed', 'media_topic', prefix=True)
        kwargs['extra_fields'] = {
            'owner_id': group.pk, 'owner_content_type_id': ContentType.objects.get_for_model(Group).pk}

        discussions = super(DiscussionRemoteManager, self).fetch(method='stream', **kwargs)
        return discussions, self.response

    @atomic
    def fetch_mediatopics(self, ids, **kwargs):

        kwargs['topic_ids'] = ','.join(map(str, ids))
        kwargs['media_limit'] = 3
        kwargs['fields'] = self.get_request_fields('media_topic', prefix=True)

        return super(DiscussionRemoteManager, self).fetch(method='mget', **kwargs)


class CommentRemoteManager(OdnoklassnikiTimelineManager):

    def parse_response(self, response, extra_fields=None):
        return super(CommentRemoteManager, self).parse_response(response.get('comments', []), extra_fields)

    @fetch_all(has_more='has_more')
    def get(self, discussion, count=100, **kwargs):
        kwargs['discussionId'] = discussion.id
        kwargs['discussionType'] = discussion.object_type
        kwargs['count'] = int(count)
        kwargs['extra_fields'] = {'discussion_id': discussion.id}

        comments = super(CommentRemoteManager, self).get(**kwargs)

        return comments, self.response

    @atomic
    def fetch(self, discussion, **kwargs):
        '''
        Get all comments, reverse order and save them, because we need to store reply_to_comment relation
        '''
        comments = super(CommentRemoteManager, self).fetch(discussion=discussion, **kwargs)

        discussion.comments_count = comments.count()
        discussion.save()

        return comments


class Discussion(OdnoklassnikiPKModel):

    methods_namespace = ''
    remote_pk_field = 'object_id'

    owner_content_type = models.ForeignKey(ContentType, related_name='odnoklassniki_discussions_owners')
    owner_id = models.BigIntegerField(db_index=True)
    owner = generic.GenericForeignKey('owner_content_type', 'owner_id')

    author_content_type = models.ForeignKey(ContentType, related_name='odnoklassniki_discussions_authors')
    author_id = models.BigIntegerField(db_index=True)
    author = generic.GenericForeignKey('author_content_type', 'author_id')

    object_type = models.CharField(max_length=20, choices=DISCUSSION_TYPE_CHOICES, default=DISCUSSION_TYPE_DEFAULT)
    title = models.TextField()
    message = models.TextField()

    date = models.DateTimeField()
    last_activity_date = models.DateTimeField(null=True)
    last_user_access_date = models.DateTimeField(null=True)

    new_comments_count = models.PositiveIntegerField(default=0)
    comments_count = models.PositiveIntegerField(default=0)
    likes_count = models.PositiveIntegerField(default=0)
    reshares_count = models.PositiveIntegerField(default=0)

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
        'mget': 'mediatopic.getByIds',
    })

#     def __unicode__(self):
#         return self.name

    class Meta:
        verbose_name = _('Odnoklassniki discussion')
        verbose_name_plural = _('Odnoklassniki discussions')

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
                from odnoklassniki_groups.models import Group
                entities['groups'] += [Group.remote.get_or_create_from_resource(resource)]
            for field in ['users', 'groups']:
                entities[field] = dict([(instance.id, instance) for instance in entities[field]])

            # set owner
            if self.ref_objects:
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
                    log.warning("Imposible to find author with ID=%s in entities of duscussion ID=%s" %
                                (self.author_id, self.id))
                    self.author_id = None

        if self.owner and not self.author_id:
            # of no author_id (owner_uid), so it's equal to owner from ref_objects
            self.author = self.owner

        if self.author_id and not self.author:
            self.author = self.author_content_type.model_class().objects.get_or_create(pk=self.author_id)[0]

        if self.owner_id and not self.owner:
            self.owner = self.owner_content_type.model_class().objects.get_or_create(pk=self.owner_id)[0]

        return super(Discussion, self).save(*args, **kwargs)

    @property
    def refresh_kwargs(self):
        return {'id': self.id, 'type': self.object_type or DISCUSSION_TYPE_DEFAULT}

    @property
    def slug(self):
        return '%s/topic/%s' % (self.owner.slug, self.id)

    def parse(self, response):
        from odnoklassniki_groups.models import Group
        if 'discussion' in response:
            response.update(response.pop('discussion'))

        # Discussion.remote.fetch_one
        if 'entities' in response and 'media_topics' in response['entities'] \
            and len(response['entities']['media_topics']) == 1:
                response.update(response['entities'].pop('media_topics')[0])

        # media_topics
        if 'like_summary' in response:
            response['likes_count'] = response['like_summary']['count']
            response.pop('like_summary')
        if 'reshare_summary' in response:
            response['reshares_count'] = response['reshare_summary']['count']
            response.pop('reshare_summary')
        if 'discussion_summary' in response:
            response['comments_count'] = response['discussion_summary']['comments_count']
            response.pop('discussion_summary')
        if 'author_ref' in response:
            i = response.pop('author_ref').split(':')
            response['author_id'] = i[1]
            self.author_content_type = ContentType.objects.get(app_label='odnoklassniki_%ss' % i[0], model=i[0])
        if 'owner_ref' in response:
            i = response.pop('owner_ref').split(':')
            response['owner_id'] = i[1]
            self.owner_content_type = ContentType.objects.get(app_label='odnoklassniki_%ss' % i[0], model=i[0])
        if 'created_ms' in response:
            response['date'] = response.pop('created_ms') / 1000
        if 'media' in response:
            response['title'] = response['media'][0]['text']

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
        if 'message' in response and '{media_topic' in response['message']:
            regexp = r'{media_topic:?(\d+)?}'
            m = re.findall(regexp, response['message'])
            if len(m):
                response['id'] = m[0]
                response['message'] = re.sub(regexp, '', response['message'])

        return super(Discussion, self).parse(response)

    def fetch_comments(self, **kwargs):
        return Comment.remote.fetch(discussion=self, **kwargs)

    def update_likes_count(self, instances, *args, **kwargs):
        users = User.objects.filter(pk__in=instances)
        self.like_users = users
        self.likes_count = len(instances)
        self.save()
        return users

    @atomic
    @fetch_all(return_all=update_likes_count, has_more=None)
    def fetch_likes(self, count=100, **kwargs):
        kwargs['discussionId'] = self.id
        kwargs['discussionType'] = self.object_type
        kwargs['count'] = int(count)
#        kwargs['fields'] = Discussion.remote.get_request_fields('user')

        response = Discussion.remote.api_call(method='get_likes', **kwargs)
        # has_more not in dict and we need to handle pagination manualy
        if 'users' not in response:
            response.pop('anchor', None)
            users_ids = []
        else:
            users_ids = list(User.remote.get_or_create_from_resources_list(
                response['users']).values_list('pk', flat=True))

        return users_ids, response


class Comment(OdnoklassnikiModel):

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

    reply_to_author_content_type = models.ForeignKey(
        ContentType, null=True, related_name='odnoklassniki_comments_reply_to_authors')
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

    class Meta:
        verbose_name = _('Odnoklassniki comment')
        verbose_name_plural = _('Odnoklassniki comments')

    @property
    def slug(self):
        return self.discussion.slug

    def save(self, *args, **kwargs):
        self.owner = self.discussion.owner

        if self.author_id and not self.author:
            if self.author_type == 'GROUP':
                if self.author_id == self.owner_id:
                    self.author = self.owner
                else:
                    from odnoklassniki_groups.models import Group
                    try:
                        self.author = Group.remote.fetch(ids=[self.author_id])[0]
                    except IndexError:
                        raise Exception("Can't fetch Odnoklassniki comment's group-author with ID %s" % self.author_id)
            else:
                try:
                    self.author = User.objects.get(pk=self.author_id)
                except User.DoesNotExist:
                    try:
                        self.author = User.remote.fetch(ids=[self.author_id])[0]
                    except IndexError:
                        raise Exception("Can't fetch Odnoklassniki comment's user-author with ID %s" % self.author_id)

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
                log.error("Try to save comment ID=%s with reply_to_comment_id=%s that doesn't exist in DB" %
                          (self.id, self.reply_to_comment_id))
                self.reply_to_comment = None

        return super(Comment, self).save(*args, **kwargs)

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

    def update_likes_count(self, instances, *args, **kwargs):
        users = User.objects.filter(pk__in=instances)
        self.like_users = users
        self.likes_count = len(instances)
        self.save()
        return users

    @atomic
    @fetch_all(return_all=update_likes_count, has_more=None)
    def fetch_likes(self, count=100, **kwargs):
        kwargs['comment_id'] = self.id
        kwargs['discussionId'] = self.discussion.id
        kwargs['discussionType'] = self.discussion.object_type
        kwargs['count'] = int(count)
#        kwargs['fields'] = Comment.remote.get_request_fields('user')

        response = Comment.remote.api_call(method='get_likes', **kwargs)
        # has_more not in dict and we need to handle pagination manualy
        if 'users' not in response:
            response.pop('anchor', None)
            users_ids = []
        else:
            users_ids = list(User.remote.get_or_create_from_resources_list(
                response['users']).values_list('pk', flat=True))

        return users_ids, response
