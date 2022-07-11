# -*- coding: utf-8 -*-

from collective.iconifiedcategory.utils import _categorized_elements
from imio.annex.content.annex import IAnnex
from plone.restapi.interfaces import IFieldSerializer
from plone.restapi.interfaces import ISerializeToJson
from plone.restapi.interfaces import ISerializeToJsonSummary
from plonemeeting.restapi.serializer.base import BaseDXSerializeFolderToJson
from plonemeeting.restapi.serializer.summary import PMBrainJSONSummarySerializer
from Products.PloneMeeting.utils import get_dx_field
from zope.component import adapter
from zope.component import queryMultiAdapter
from zope.interface import implementer
from zope.interface import Interface


class BaseSerializeAnnexToJson(object):
    """ """

    def _include_custom(self, obj, result):
        """Include "file" by default."""
        if self.fullobjects or \
           "file" in self.metadata_fields or \
           self.get_param('include_base_data', True):
            field = get_dx_field(obj, "file")
            # serialize the field
            serializer = queryMultiAdapter(
                (field, obj, self.request), IFieldSerializer
            )
            value = serializer()
            result["file"] = value
        return result

    def _additional_values(self, result, additional_values):
        """Let include every values available from
           parent's categorized_elements."""
        ignored_values = ["allowedRolesAndUsers", "last_updated", "visible_for_groups"]
        parent = self.context.aq_parent
        infos = _categorized_elements(parent)[self.context.UID()]
        values = {
            k: v for k, v in infos.items()
            if k not in result and not (k.endswith("_url") or k in ignored_values) and
            ("*" in additional_values or k in additional_values)
        }

        result.update(values)
        return result


@implementer(ISerializeToJson)
@adapter(IAnnex, Interface)
class SerializeToJson(BaseSerializeAnnexToJson, BaseDXSerializeFolderToJson):
    """ """


@implementer(ISerializeToJsonSummary)
@adapter(IAnnex, Interface)
class SerializeToJsonSummary(BaseSerializeAnnexToJson, PMBrainJSONSummarySerializer):
    """ """
