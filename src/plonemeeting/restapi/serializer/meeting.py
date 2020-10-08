# -*- coding: utf-8 -*-

from plone import api
from plone.restapi.interfaces import ISerializeToJson
from plonemeeting.restapi.serializer.base import BaseATSerializeToJson
from Products.PloneMeeting.interfaces import IMeeting
from zope.component import adapter
from zope.interface import implementer
from zope.interface import Interface


@implementer(ISerializeToJson)
@adapter(IMeeting, Interface)
class SerializeToJson(BaseATSerializeToJson):
    """ """

    def _additional_values(self, result):
        """ """
        tool = api.portal.get_tool('portal_plonemeeting')
        # add some formatted values
        result["formatted_assembly"] = self.context.displayStrikedAssembly()
        result["formatted_date"] = tool.formatMeetingDate(
            self.context, short=True, withHour=True)
        result["formatted_date_short"] = tool.formatMeetingDate(
            self.context, short=True, withHour=False)
        result["formatted_date_long"] = tool.formatMeetingDate(
            self.context, short=False, withHour=True)

        return result
