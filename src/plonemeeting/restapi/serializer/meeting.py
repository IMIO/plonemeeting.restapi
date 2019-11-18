# -*- coding: utf-8 -*-

from plone import api
from plone.restapi.interfaces import ISerializeToJson
from plone.restapi.deserializer import boolean_value
from plonemeeting.restapi.serializer.base import BaseSerializeToJson
from Products.PloneMeeting.interfaces import IMeeting
from zope.component import adapter
from zope.interface import implementer
from zope.interface import Interface
from plone.restapi.batching import HypermediaBatch
from zope.component import getMultiAdapter


@implementer(ISerializeToJson)
@adapter(IMeeting, Interface)
class SerializeToJson(BaseSerializeToJson):

    def _serialized_data(self):
        ''' '''
        result = super(SerializeToJson, self)._serialized_data()

        include_items = self.request.form.get("include_items")
        include_items = boolean_value(include_items)
        if include_items:
            query = self._build_query()

            brains = api.content.find(**query)

            batch = HypermediaBatch(self.request, brains)

            result["@id"] = batch.canonical_url
            result["items_total"] = batch.items_total
            if batch.links:
                result["batching"] = batch.links

            result["items"] = getMultiAdapter(
                (brains, self.request), ISerializeToJson
            )(fullobjects=True)["items"]
        return result
