# -*- coding: utf-8 -*-

from plone import api
from plone.restapi.interfaces import ISerializeToJson
from plone.restapi.interfaces import ISerializeToJsonSummary
from plonemeeting.restapi.serializer.base import BaseDXSerializeToJson
from plonemeeting.restapi.serializer.summary import PMBrainJSONSummarySerializer
from Products.PloneMeeting.content.meeting import IMeeting
from zope.component import adapter
from zope.interface import implementer
from zope.interface import Interface


class SerializeMeetingToJsonBase(object):
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


@implementer(ISerializeToJson)
@adapter(IMeeting, Interface)
class SerializeToJson(SerializeMeetingToJsonBase, BaseDXSerializeToJson):
    """ """

    def __call__(self, version=None, include_items=False):
        """Change include_items=False by default."""
        # fullobjects for extra_includes?
        self.extra_include_fullobjects = False
        if "extra_include_fullobjects" in self.request.form:
            self.extra_include_fullobjects = True
        # override include_items
        result = super(SerializeToJson, self).__call__(
            version=version, include_items=include_items
        )
        return result


@implementer(ISerializeToJsonSummary)
@adapter(IMeeting, Interface)
class SerializeToJsonSummary(SerializeMeetingToJsonBase, PMBrainJSONSummarySerializer):
    """ """
