# -*- coding: utf-8 -*-

from plone.restapi.interfaces import ISerializeToJsonSummary
from plone.restapi.serializer.summary import DefaultJSONSummarySerializer
from plonemeeting.restapi.serializer.base import include_annexes
from Products.ZCatalog.interfaces import ICatalogBrain
from zope.component import adapter
from zope.interface import implementer
from zope.interface import Interface


@implementer(ISerializeToJsonSummary)
@adapter(ICatalogBrain, Interface)
class PMJSONSummarySerializer(DefaultJSONSummarySerializer):
    """Override the default ISerializeToJsonSummary adapter."""

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self):
        summary = super(PMJSONSummarySerializer, self).__call__()
        # annexes
        obj = self.context.getObject()
        summary.update(include_annexes(obj, self.request, fullobjects=False))

        return summary
