# -*- coding: utf-8 -*-

from plone import api
from plone.restapi.interfaces import ISerializeToJson
from plone.restapi.interfaces import ISerializeToJsonSummary
from plone.restapi.serializer.user import BaseSerializer
from plonemeeting.restapi.interfaces import IPMRestapiLayer
from Products.CMFCore.interfaces._tools import IMemberData
from Products.CMFPlone.utils import safe_unicode
from zope.component import adapter
from zope.interface import implementer


class PMBaseSerializer(BaseSerializer):

    def __call__(self):
        data = super(PMBaseSerializer, self).__call__()
        if "include_groups" in self.request.form:
            tool = api.portal.get_tool("portal_plonemeeting")
            groups = tool.get_plone_groups_for_user(userId=self.context.id, the_objects=True)
            data["groups"] = [{"token": group.id,
                               "title": safe_unicode(group.getProperty("title"))}
                              for group in groups]
        return data


@implementer(ISerializeToJson)
@adapter(IMemberData, IPMRestapiLayer)
class SerializeUserToJson(PMBaseSerializer):
    pass


@implementer(ISerializeToJsonSummary)
@adapter(IMemberData, IPMRestapiLayer)
class SerializeUserToJsonSummary(PMBaseSerializer):
    pass
