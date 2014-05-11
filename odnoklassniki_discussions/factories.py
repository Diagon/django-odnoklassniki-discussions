from odnoklassniki_users.factories import UserFactory
from odnoklassniki_groups.factories import GroupFactory
from models import Discussion, Comment
from datetime import datetime
from random import randrange
import factory


class DiscussionFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Discussion

    id = factory.Sequence(lambda n: n)
    date = datetime.now()
    last_activity_date = datetime.now()
    last_user_access_date = datetime.now()

    owner = factory.SubFactory(GroupFactory)
    author = factory.SubFactory(UserFactory)


class CommentFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Comment

    id = factory.Sequence(lambda n: n)
    date = datetime.now()

    discussion = factory.SubFactory(DiscussionFactory)
    author = factory.SubFactory(UserFactory)
