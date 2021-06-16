# -*- coding: utf-8 -*-

from plone.restapi.deserializer import boolean_value
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


class BaseSerializeToJson(object):
    """ """
    def _extra_include(self, result):
        """ """
        return result

    def _additional_values(self, result):
        """ """
        return result

    def _after__call__(self, result):
        """ """
        # fullobjects for extra_includes?
        self.extra_include_fullobjects = False
        if "extra_include_fullobjects" in self.request.form:
            self.extra_include_fullobjects = True

        # only call _extra_include if relevant
        if self.request.form.get("extra_include", []):
            result = self._extra_include(result)
        # when fullobjects, additional_values default is True
        # when not fullobjects, additional_values default is False
        if (self.request.form.get("fullobjects", False) and
            boolean_value(self.request.form.get("additional_values", True))) or \
           boolean_value(self.request.form.get("additional_values", False)):
            result = self._additional_values(result)
        return result

    def __call__(self, version=None, include_items=True):
        """ """
        result = super(BaseSerializeToJson, self).__call__(
            version=version, include_items=include_items
        )
        result = self._after__call__(result)
        return result


@implementer(ISerializeToJson)
@adapter(IMeetingContent, Interface)
class BaseATSerializeToJson(BaseSerializeToJson, ATSerializeFolderToJson):
    """ """


@implementer(ISerializeToJson)
@adapter(Interface, Interface)
class BaseDXSerializeToJson(BaseSerializeToJson, DXSerializeFolderToJson):
    """ """
