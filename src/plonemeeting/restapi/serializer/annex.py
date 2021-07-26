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

    def _include_categorized_infos(self, obj):
        """Include iconificategory related attributes, extend result
           with infos managed by collective.iconifiedcategory if not already in the result
           ignore also _url related infos that use relative URi."""
        result = {}

        if self.include_all or self._get_param('include_categorized_infos'):
            parent = obj.aq_parent
            infos = _categorized_elements(parent)[obj.UID()]
            result = {
                k: v for k, v in infos.items()
                if k not in result and not k.endswith("_url")
            }

        return result

    def _include_custom(self, obj, result):
        result.update(self._include_categorized_infos(obj))
        return result
