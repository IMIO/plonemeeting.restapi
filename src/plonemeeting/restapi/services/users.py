# -*- coding: utf-8 -*-

from plone.restapi.services.users.get import UsersGet
from plonemeeting.restapi.utils import may_access_config_endpoints
from zope.interface import implementer
from zope.publisher.interfaces import IPublishTraverse


@implementer(IPublishTraverse)
class PMUsersGet(UsersGet):
    def __init__(self, context, request):
        super(UsersGet, self).__init__(context, request)
        self.params = []
        self.query = self.request.form.copy()

    def has_permission_to_query(self):
        return may_access_config_endpoints()

    def has_permission_to_enumerate(self):
        return may_access_config_endpoints()

    def has_permission_to_access_user_info(self):
        return may_access_config_endpoints()
