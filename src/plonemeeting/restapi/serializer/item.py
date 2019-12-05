# -*- coding: utf-8 -*-

from plone.restapi.interfaces import ISerializeToJson
from plonemeeting.restapi.serializer.base import BaseATSerializeToJson
from Products.PloneMeeting.interfaces import IMeetingItem
from zope.component import adapter
from zope.interface import implementer
from zope.interface import Interface


@implementer(ISerializeToJson)
@adapter(IMeetingItem, Interface)
class SerializeToJson(BaseATSerializeToJson):
    ''' '''

    def _get_public_deliberation(self):
        ''' '''
        view = self.context.restrictedTraverse('document-generation')
        helper = view.get_generation_context_helper()
        return helper.print_public_deliberation()

    def __call__(self, version=None, include_items=True):
        ''' '''

        result = super(SerializeToJson, self).__call__(
            version=version, include_items=include_items)

        # add some formatted values
        result['formatted_itemAssembly'] = self.context.displayStrikedItemAssembly()
        result['formatted_itemNumber'] = self.context.getItemNumber(for_display=True)
        result['formatted_deliberation'] = self._get_deliberation()
        result['formatted_public_deliberation'] = self._get_public_deliberation()
        return result
