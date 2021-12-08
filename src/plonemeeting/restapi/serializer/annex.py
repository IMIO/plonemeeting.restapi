# -*- coding: utf-8 -*-

from collective.iconifiedcategory.utils import _categorized_elements
from imio.annex.content.annex import IAnnex
from plone.restapi.interfaces import ISerializeToJson
from plonemeeting.restapi.serializer.base import BaseDXSerializeFolderToJson
from zope.component import adapter
from zope.interface import implementer
from zope.interface import Interface


@implementer(ISerializeToJson)
@adapter(IAnnex, Interface)
class AnnexSerializeToJson(BaseDXSerializeFolderToJson):
    """ """

    def _additional_values(self, result, additional_values):
        """Let include every values available from
           parent's categorized_elements."""

        ignored_values = ["allowedRolesAndUsers", "last_updated", "visible_for_groups"]
        parent = self.context.aq_parent
        infos = _categorized_elements(parent)[self.context.UID()]
        values = {
            k: v for k, v in infos.items()
            if k not in result and not (k.endswith("_url") or k in ignored_values)
            and (additional_values == "*" or k in additional_values)
        }

        result.update(values)
        return result
