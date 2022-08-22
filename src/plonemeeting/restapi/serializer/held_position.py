# -*- coding: utf-8 -*-

from plone import api
from plone.restapi.interfaces import ISerializeToJson
from plone.restapi.interfaces import ISerializeToJsonSummary
from plonemeeting.restapi.serializer.base import BaseDXSerializeFolderToJson
from plonemeeting.restapi.serializer.base import serialize_person
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
            result["extra_include_person"] = serialize_person(
                self.context, self)
        return result


@implementer(ISerializeToJson)
@adapter(IPMHeldPosition, Interface)
class SerializeToJson(SerializeHeldPositionToJsonBase, BaseDXSerializeFolderToJson):
    """ """


@implementer(ISerializeToJsonSummary)
@adapter(IPMHeldPosition, Interface)
class SerializeToJsonSummary(SerializeHeldPositionToJsonBase, PMBrainJSONSummarySerializer):
    """ """
