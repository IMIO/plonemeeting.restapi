# -*- coding: utf-8 -*-

from plone import api
from plone.restapi.interfaces import ISerializeToJson
from plone.restapi.interfaces import ISerializeToJsonSummary
from plonemeeting.restapi.serializer.base import BaseDXSerializeFolderToJson
from plonemeeting.restapi.serializer.base import serialize_extra_include_annexes
from plonemeeting.restapi.serializer.base import serialize_pod_templates
from plonemeeting.restapi.serializer.summary import PMBrainJSONSummarySerializer
from Products.PloneMeeting.content.meeting import IMeeting
from zope.component import adapter
from zope.interface import implementer
from zope.interface import Interface


class SerializeMeetingToJsonBase(object):
    """ """

    def _available_extra_includes(self, result):
        """ """
        result["@extra_includes"] = ["annexes", "pod_templates"]
        return result

    def _extra_include(self, result):
        """ """
        extra_include = self._get_asked_extra_include()
        if "pod_templates" in extra_include:
            result["extra_include_pod_templates"] = serialize_pod_templates(
                self.context, self)
        if "annexes" in extra_include:
            result = serialize_extra_include_annexes(result, self)
        return result

    def _additional_values(self, result, additional_values):
        """ """
        # add some formatted values
        tool = api.portal.get_tool('portal_plonemeeting')
        # Products.PloneMeeting 4.1/4.2 compatibility
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
        return result


@implementer(ISerializeToJson)
@adapter(IMeeting, Interface)
class SerializeToJson(SerializeMeetingToJsonBase, BaseDXSerializeFolderToJson):
    """ """


@implementer(ISerializeToJsonSummary)
@adapter(IMeeting, Interface)
class SerializeToJsonSummary(SerializeMeetingToJsonBase, PMBrainJSONSummarySerializer):
    """ """
