# -*- coding: utf-8 -*-

from plone.restapi.services.users.get import UsersGet
from plonemeeting.restapi.utils import get_poweraccess_configs
from zope.interface import implementer
from zope.publisher.interfaces import IPublishTraverse


@implementer(IPublishTraverse)
class PMUsersGet(UsersGet):
    def __init__(self, context, request):
        super(UsersGet, self).__init__(context, request)
        self.params = []
        self.query = self.request.form.copy()

    def has_permission_to_query(self):
        return get_poweraccess_configs()

    def has_permission_to_enumerate(self):
        return get_poweraccess_configs()

    def has_permission_to_access_user_info(self):
        return get_poweraccess_configs()
