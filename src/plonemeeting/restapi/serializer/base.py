# -*- coding: utf-8 -*-

from plone.restapi.interfaces import ISerializeToJson
from plone.restapi.serializer.atcontent import (
    SerializeFolderToJson as ATSerializeFolderToJson,
)
from plone.restapi.serializer.dxcontent import (
    SerializeFolderToJson as DXSerializeFolderToJson,
)
from Products.PloneMeeting.interfaces import IMeetingContent
from zope.component import adapter
from zope.interface import implementer
from zope.interface import Interface


@implementer(ISerializeToJson)
@adapter(IMeetingContent, Interface)
class BaseATSerializeToJson(ATSerializeFolderToJson):
    """ """

    def _extra_include(self, result):
        """ """
        return result

    def _additional_values(self, result):
        """ """
        return result

    def __call__(self, version=None, include_items=True):
        """ """

        result = super(BaseATSerializeToJson, self).__call__(
            version=version, include_items=include_items
        )

        result = self._extra_include(result)
        result = self._additional_values(result)

        return result


@implementer(ISerializeToJson)
@adapter(Interface, Interface)
class BaseDXSerializeToJson(DXSerializeFolderToJson):
    """ """
