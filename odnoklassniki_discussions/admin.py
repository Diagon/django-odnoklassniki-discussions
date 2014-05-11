# -*- coding: utf-8 -*-
from django.contrib import admin
try:
    from django.template.defaultfilters import truncatewords
except ImportError:
    from django.utils.text import truncate_words as truncatewords
from odnoklassniki_api.admin import OdnoklassnikiModelAdmin, GenericRelationListFilter
from models import Discussion, Comment

class WallOwnerListFilter(GenericRelationListFilter):
    title = u'Владелец стены'

    ct_field_name = 'owner_content_type'
    id_field_name = 'owner_id'
    field_name = 'owner'

class DiscussionListFilter(admin.SimpleListFilter):
    title = u'Сообщение'
    parameter_name = 'discussion'

    field_name = 'discussion'

    separator = '-'
    ct_field_name = 'owner_content_type'
    id_field_name = 'owner_id'
    parent_parameter_name = 'owner'

    def lookups(self, request, model_admin):
        parent_value = request.REQUEST.get(self.parent_parameter_name)
        if parent_value:
            ct_value, id_value = parent_value.split(self.separator)
            return [(str(instance.post_id), truncatewords(instance.post.text, 5)) for instance in model_admin.model.objects.order_by().filter(**{self.ct_field_name: ct_value, self.id_field_name: id_value}).distinct(self.field_name)]

    def queryset(self, request, queryset):
        parent_value = request.REQUEST.get(self.parent_parameter_name)
        if parent_value and self.value():
            ct_value, id_value = parent_value.split(self.separator)
            return queryset.filter(**{self.ct_field_name: ct_value, self.id_field_name: id_value, self.field_name: self.value()})

class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    can_delete = False
    fields = ('author','text','date','likes_count')
    readonly_fields = fields

class DiscussionAdmin(OdnoklassnikiModelAdmin):
    list_display = ('owner','message','author','ok_link','object_type','date','comments_count','likes_count')#,'reposts')
    list_display_links = ('message',)
    list_filter = (WallOwnerListFilter,)
    search_fields = ('message','title','id')
#    exclude = ('like_users','repost_users',)
    inlines = [CommentInline]

class CommentAdmin(OdnoklassnikiModelAdmin):
    list_display = ('author','text','discussion','date','likes_count')
    search_fields = ('text','id')
    list_filter = (WallOwnerListFilter, DiscussionListFilter,)

admin.site.register(Discussion, DiscussionAdmin)
admin.site.register(Comment, CommentAdmin)