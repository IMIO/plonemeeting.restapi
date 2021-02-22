# -*- coding: utf-8 -*-

from plone import api
from plone.restapi.interfaces import ISerializeToJson
from plonemeeting.restapi.serializer.base import BaseDXSerializeToJson
from Products.PloneMeeting.content.meeting import IMeeting
from zope.component import adapter
from zope.interface import implementer
from zope.interface import Interface


@implementer(ISerializeToJson)
@adapter(IMeeting, Interface)
class SerializeToJson(BaseDXSerializeToJson):
    """ """

    def _additional_values(self, result):
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
