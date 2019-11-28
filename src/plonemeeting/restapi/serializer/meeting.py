# -*- coding: utf-8 -*-

from plone.restapi.interfaces import ISerializeToJson
from plonemeeting.restapi.serializer.base import BaseATSerializeToJson
from Products.PloneMeeting.interfaces import IMeeting
from zope.component import adapter
from zope.interface import implementer
from zope.interface import Interface


@implementer(ISerializeToJson)
@adapter(IMeeting, Interface)
class SerializeToJson(BaseATSerializeToJson):
    ''' '''

    def __call__(self, version=None, include_items=True):
        ''' '''

        result = super(SerializeToJson, self).__call__(
            version=version, include_items=include_items)

        # add some formatted values
        result['formatted_assembly'] = self.context.displayStrikedAssembly()
        return result
