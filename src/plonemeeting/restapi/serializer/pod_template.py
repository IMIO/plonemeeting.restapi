# -*- coding: utf-8 -*-

from collective.documentgenerator.content.pod_template import IConfigurablePODTemplate
from imio.helpers.content import base_hasattr
from plone.restapi.interfaces import ISerializeToJson
from plone.restapi.interfaces import ISerializeToJsonSummary
from plonemeeting.restapi.serializer.base import BaseDXSerializeFolderToJson
from plonemeeting.restapi.serializer.summary import PMBrainJSONSummarySerializer
from zope.component import adapter
from zope.interface import implementer
from zope.interface import Interface


class BaseSerializePodTemplateToJson(object):
    """ """

    def _include_custom(self, obj, result):
        """Include outputs (format/url)."""
        if base_hasattr(self, "original_context"):
            result["outputs"] = []
            original_context_url = self.original_context.absolute_url()
            url_pattern = "{0}/document-generation?template_uid={1}&output_format={2}"
            for output_format in self.context.get_available_formats():
                data = {}
                data["format"] = output_format
                data["url"] = url_pattern.format(
                    original_context_url, result["UID"], output_format)
                result["outputs"].append(data)
        return result


@implementer(ISerializeToJson)
@adapter(IConfigurablePODTemplate, Interface)
class SerializeToJson(BaseSerializePodTemplateToJson, BaseDXSerializeFolderToJson):
    """ """


@implementer(ISerializeToJsonSummary)
@adapter(IConfigurablePODTemplate, Interface)
class SerializeToJsonSummary(BaseSerializePodTemplateToJson, PMBrainJSONSummarySerializer):
    """ """
