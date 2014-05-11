Django Odnoklassniki Discussions
================================

[![PyPI version](https://badge.fury.io/py/django-odnoklassniki-discussions.png)](http://badge.fury.io/py/django-odnoklassniki-discussions) [![Build Status](https://travis-ci.org/ramusus/django-odnoklassniki-discussions.png?branch=master)](https://travis-ci.org/ramusus/django-odnoklassniki-discussions) [![Coverage Status](https://coveralls.io/repos/ramusus/django-odnoklassniki-discussions/badge.png?branch=master)](https://coveralls.io/r/ramusus/django-odnoklassniki-discussions)

Приложение позволяет взаимодействовать с дискуссиями соц. сети Одноклассники, их статистикой и пользователями групп через OK API используя стандартные модели Django

Установка
---------

    pip install django-odnoklassniki-discussions

В `settings.py` необходимо добавить:

    INSTALLED_APPS = (
        ...
        'oauth_tokens',
        'taggit',
        'odnoklassniki_api',
        'odnoklassniki_groups',
        'odnoklassniki_users',
        'odnoklassniki_discussions',
    )

    # oauth-tokens settings
    OAUTH_TOKENS_HISTORY = True                                             # to keep in DB expired access tokens
    OAUTH_TOKENS_ODNOKLASSNIKI_CLIENT_PUBLIC = ''                           # application public key
    OAUTH_TOKENS_ODNOKLASSNIKI_CLIENT_SECRET = ''                           # application secret key
    OAUTH_TOKENS_ODNOKLASSNIKI_SCOPE = ['']                                 # application scopes
    OAUTH_TOKENS_ODNOKLASSNIKI_USERNAME = ''                                # user login
    OAUTH_TOKENS_ODNOKLASSNIKI_PASSWORD = ''                                # user password

Покрытие методов API
--------------------

* [discussions.getList](http://apiok.ru/wiki/display/api/discussions.getList) – получение списка дискуссий;
* [discussions.get](http://apiok.ru/wiki/display/api/discussions.get) – получение подробной информации о дискуссии с возможностью в одном запросе получить информацию об упоминаемых в дискуссии объектах;
* [discussions.getDiscussionLikes](http://apiok.ru/wiki/display/api/discussions.getDiscussionLikes) – получить список пользователей, поставивших "Класс" для дискуссии;
* [discussions.getComments](http://apiok.ru/wiki/display/api/discussions.getComments) – получение списка комментариев к дискуссии;
* [discussions.getComment](http://apiok.ru/wiki/display/api/discussions.getComment) – получение информации о комментарии к дискуссии;
* [discussions.getCommentLikes](http://apiok.ru/wiki/display/api/discussions.getCommentLikes) – получение списка пользователей, поставивших "Класс" для указанного комментария;
* [stream.get](http://apiok.ru/wiki/display/api/stream.get);

Примеры использования
---------------------

### Получение группы

    >>> from odnoklassniki_discussions.models import Group
    >>> Group.remote.fetch(ids=[47241470410797])
    [<Group: Кока-Кола>]

### Получение подписчиков группы

Для этого необходимо установить дополнительно приложения:
[`django-odnoklassniki-users`](http://github.com/ramusus/django-odnoklassniki-users/) и добавить его в `INSTALLED_APPS`
[`django-m2m-history`](http://github.com/ramusus/django-m2m-history/)

    >>> from odnoklassniki_discussions.models import Group
    >>> group = Group.remote.fetch(ids=[47241470410797])[0]
    >>> group.update_users()
    >>> group.users.count()
    987