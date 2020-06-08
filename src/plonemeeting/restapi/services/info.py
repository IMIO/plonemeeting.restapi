# -*- coding: utf-8 -*-

from plone import api
from plone.restapi.services import Service


class WSInfosGet(Service):
    """Returns informations about installed versions."""

    def reply(self):
        result = {}
        for package_name in ['Products.PloneMeeting', 'imio.restapi', 'plonemeeting.restapi']:
            version = api.env.get_distribution(package_name)._version
            result[package_name] = version
        user = api.user.get_current()
        result['connected_user'] = user.getId()
        return result
