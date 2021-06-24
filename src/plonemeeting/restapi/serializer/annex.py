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
                k: v for k, v in infos.items() if k not in result and not k.endswith("_url")
            }

        return result

    def __call__(self, version=None, include_items=True):
        """ """
        result = super(AnnexSerializeToJson, self).__call__(
            version=version, include_items=include_items
        )
        version = "current" if version is None else version
        obj = self.getVersion(version)

        result.update(self._include_categorized_infos(obj))
        return result
