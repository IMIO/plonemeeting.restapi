# -*- coding: utf-8 -*-

from plone.restapi.interfaces import ISerializeToJson
from plonemeeting.restapi.serializer.base import BaseATSerializeToJson
from plonemeeting.restapi.utils import listify
from Products.PloneMeeting.interfaces import IMeetingConfig
from zope.component import adapter
from zope.component import queryMultiAdapter
from zope.interface import implementer
from zope.interface import Interface


@implementer(ISerializeToJson)
@adapter(IMeetingConfig, Interface)
class SerializeToJson(BaseATSerializeToJson):
    ''' '''

    def _extra_include(self, result):
        ''' '''
        extra_include = listify(self.request.form.get('extra_include', []))
        if 'categories' in extra_include:
            categories = self.context.getCategories()
            result['extra_include_categories'] = []
            for category in categories:
                serializer = queryMultiAdapter((category, self.request), ISerializeToJson)
                result['extra_include_categories'].append(serializer())
        if 'pod_templates' in extra_include:
            pod_templates = self.context.podtemplates.getFolderContents(full_objects=True)
            result['extra_include_pod_templates'] = []
            for pod_template in pod_templates:
                serializer = queryMultiAdapter((pod_template, self.request), ISerializeToJson)
                result['extra_include_pod_templates'].append(serializer())
        if 'searches' in extra_include:
            collections = self.context.searches.searches_items.getFolderContents(full_objects=True)
            result['extra_include_searches'] = []
            for collection in collections:
                serializer = queryMultiAdapter((collection, self.request), ISerializeToJson)
                result['extra_include_searches'].append(serializer(include_items=False))
        return result
