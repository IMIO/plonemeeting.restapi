# -*- coding: utf-8 -*-

from collective.iconifiedcategory.utils import _categorized_elements
from imio.annex.content.annex import IAnnex
from plone.restapi.interfaces import ISerializeToJson
from plone.restapi.serializer.dxcontent import SerializeToJson
from zope.component import adapter
from zope.interface import implementer
from zope.interface import Interface


@implementer(ISerializeToJson)
@adapter(IAnnex, Interface)
class AnnexSerializeToJson(SerializeToJson):
    """ """

    def __call__(self, version=None, include_items=True):
        """ """
        result = super(AnnexSerializeToJson, self).__call__(
            version=version, include_items=include_items
        )

        # include iconificategory related attributes, extend result
        # with infos managed by collective.iconifiedcategory if not already in the result
        # ignore also _url related infos that use relative URi
        parent = self.context.aq_parent
        infos = _categorized_elements(parent)[self.context.UID()]
        infos = {
            k: v for k, v in infos.items() if k not in result and not k.endswith("_url")
        }
        result.update(infos)
        return result
