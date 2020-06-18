# -*- coding: utf-8 -*-

from collective.eeafaceted.collectionwidget.content.dashboardcollection import (
    IDashboardCollection,
)
from plone.restapi.serializer.collection import SerializeCollectionToJson
from zope.component import adapter
from zope.interface import Interface


@adapter(IDashboardCollection, Interface)
class SerializeDashboardCollectionToJson(SerializeCollectionToJson):
    def __call__(self, version=None, include_items=True):
        # until parameter include_items=False is taken into account, we override this
        collection_metadata = super(SerializeCollectionToJson, self).__call__(
            version=version
        )
        results = collection_metadata
        return results
