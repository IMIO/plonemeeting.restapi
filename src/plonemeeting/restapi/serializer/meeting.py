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


# until every Products.PloneMeeting are not using version 4.2
# we need to keep backward compatibility between Meeting using AT (4.1) and DX (4.2)
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

    def _additional_values(self, result, additional_values):
        """ """
        # add some formatted values
        tool = api.portal.get_tool('portal_plonemeeting')
        # Products.PloneMeeting 4.1/4.2 compatibility
        if HAS_MEETING_DX:
            if "*" in additional_values or "formatted_assembly" in additional_values:
                result["formatted_assembly"] = self.context.get_assembly(striked=True)
            if "*" in additional_values or "formatted_date" in additional_values:
                result["formatted_date"] = tool.format_date(
                    self.context.date, short=True, with_hour=True)
            if "*" in additional_values or "formatted_date_short" in additional_values:
                result["formatted_date_short"] = tool.format_date(
                    self.context.date, short=True, with_hour=False)
            if "*" in additional_values or "formatted_date_long" in additional_values:
                result["formatted_date_long"] = tool.format_date(
                    self.context.date, short=False, with_hour=True)
        else:
            # backward compat for AT
            if "*" in additional_values or "formatted_assembly" in additional_values:
                result["formatted_assembly"] = self.context.displayStrikedAssembly()
            if "*" in additional_values or "formatted_date" in additional_values:
                result["formatted_date"] = tool.formatMeetingDate(
                    self.context, short=True, withHour=True)
            if "*" in additional_values or "formatted_date_short" in additional_values:
                result["formatted_date_short"] = tool.formatMeetingDate(
                    self.context, short=True, withHour=False)
            if "*" in additional_values or "formatted_date_long" in additional_values:
                result["formatted_date_long"] = tool.formatMeetingDate(
                    self.context, short=False, withHour=True)

        return result


@implementer(ISerializeToJson)
@adapter(IMeeting, Interface)
class SerializeToJson(SerializeMeetingToJsonBase, MeetingBaseClass):
    """ """


@implementer(ISerializeToJsonSummary)
@adapter(IMeeting, Interface)
class SerializeToJsonSummary(SerializeMeetingToJsonBase, PMBrainJSONSummarySerializer):
    """ """
