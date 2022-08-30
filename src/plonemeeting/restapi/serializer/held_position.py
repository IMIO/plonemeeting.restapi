# -*- coding: utf-8 -*-

from plone.restapi.interfaces import ISerializeToJson
from plone.restapi.interfaces import ISerializeToJsonSummary
from plonemeeting.restapi.serializer.base import BaseDXSerializeFolderToJson
from plonemeeting.restapi.serializer.summary import PMBrainJSONSummarySerializer
from Products.PloneMeeting.content.held_position import IPMHeldPosition
from zope.component import adapter
from zope.interface import implementer
from zope.interface import Interface


class SerializeHeldPositionToJsonBase(object):
    """ """

    def _available_extra_includes(self, result):
        """ """
        result["@extra_includes"] = ["person"]
        return result

    def _extra_include(self, result):
        """ """
        extra_include = self._get_asked_extra_include()
        if "person" in extra_include:
            person = self.context.get_person()
            serializer = self._get_serializer(person, "person")
            result["extra_include_person"] = serializer()
        return result

    def _include_custom(self, obj, result):
        """Include "full_title" by default."""
        if self.fullobjects or \
           "full_title" in self.metadata_fields or \
           self.get_param('include_base_data', True):
            result["full_title"] = self.context.get_full_title()
        return result


@implementer(ISerializeToJson)
@adapter(IPMHeldPosition, Interface)
class SerializeToJson(SerializeHeldPositionToJsonBase, BaseDXSerializeFolderToJson):
    """ """


@implementer(ISerializeToJsonSummary)
@adapter(IPMHeldPosition, Interface)
class SerializeToJsonSummary(SerializeHeldPositionToJsonBase, PMBrainJSONSummarySerializer):
    """ """
