# -*- coding: utf-8 -*-

from collective.iconifiedcategory.utils import get_categorized_elements
from plone.restapi.deserializer import boolean_value
from plone.restapi.interfaces import ISerializeToJson
from plonemeeting.restapi.serializer.base import BaseSerializeToJson
from Products.PloneMeeting.interfaces import IMeetingItem
from zope.component import adapter
from zope.component import getMultiAdapter
from zope.interface import implementer
from zope.interface import Interface


@implementer(ISerializeToJson)
@adapter(IMeetingItem, Interface)
class SerializeToJson(BaseSerializeToJson):
    ''' '''

    def _serialized_data(self):
        ''' '''
        result = super(SerializeToJson, self)._serialized_data()

        form = self.request.form
        include_annexes = form.get("include_annexes")
        include_annexes = boolean_value(include_annexes)
        if include_annexes:
            annexes = get_categorized_elements(self.context, result_type='objects')
            result["items_total"] = len(annexes)
            result["items"] = []
            # filters annex related
            annex_filters = {}
            for k, v in form.items():
                if k.startswith('filter_annex_'):
                    annex_filters[k[:13]] = v
            for annex in annexes:
                serialized_annex = getMultiAdapter(
                    (annex, self.request), ISerializeToJson)()
                keep_annex = True
                for k, v in annex_filters.items():
                    if serialized_annex.get(k, None) != v:
                        keep_annex = False
                        break
                if keep_annex:
                    result["items"].append(serialized_annex)
        return result
