# -*- coding: utf-8 -*-

from plone.restapi.interfaces import ISerializeToJsonSummary
from plone.restapi.serializer.summary import DefaultJSONSummarySerializer
from Products.ZCatalog.interfaces import ICatalogBrain
from zope.component import adapter
from zope.interface import implementer
from zope.interface import Interface


@implementer(ISerializeToJsonSummary)
@adapter(ICatalogBrain, Interface)
class PMJSONSummarySerializer(DefaultJSONSummarySerializer):
    """Override the default ISerializeToJsonSummary adapter."""
