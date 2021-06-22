# -*- coding: utf-8 -*-

from plone import api
from plone.restapi.interfaces import ISerializeToJson
from plone.restapi.interfaces import ISerializeToJsonSummary
from plonemeeting.restapi.serializer.base import BaseATSerializeFolderToJson
from plonemeeting.restapi.serializer.base import BaseDXSerializeFolderToJson
from plonemeeting.restapi.serializer.summary import PMBrainJSONSummarySerializer
from zope.component import adapter
from zope.interface import implementer
from zope.interface import Interface

HAS_MEETING_DX = False
MeetingBaseClass = BaseATSerializeFolderToJson
try:
    from Products.PloneMeeting.content.meeting import IMeeting
    HAS_MEETING_DX = True
    MeetingBaseClass = BaseDXSerializeFolderToJson
except ImportError:
    from Products.PloneMeeting.interfaces import IMeeting


class SerializeMeetingToJsonBase(object):
    """ """

    def _include_additional_values(self, result):
        """ """
        tool = api.portal.get_tool('portal_plonemeeting')
        # add some formatted values
        result["formatted_assembly"] = self.context.get_assembly(striked=True)
        result["formatted_date"] = tool.format_date(
            self.context.date, short=True, with_hour=True)
        result["formatted_date_short"] = tool.format_date(
            self.context.date, short=True, with_hour=False)
        result["formatted_date_long"] = tool.format_date(
            self.context.date, short=False, with_hour=True)

        return result


@implementer(ISerializeToJson)
@adapter(IMeeting, Interface)
class SerializeToJson(SerializeMeetingToJsonBase, MeetingBaseClass):
    """ """


@implementer(ISerializeToJsonSummary)
@adapter(IMeeting, Interface)
class SerializeToJsonSummary(SerializeMeetingToJsonBase, PMBrainJSONSummarySerializer):
    """ """
