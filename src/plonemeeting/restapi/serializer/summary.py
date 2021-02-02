# -*- coding: utf-8 -*-

from plone.restapi.interfaces import ISerializeToJsonSummary
from imio.restapi.serializer.base import DefaultJSONSummarySerializer
from Products.ZCatalog.interfaces import ICatalogBrain
from OFS.interfaces import IItem
from zope.component import adapter
from zope.interface import implementer
from zope.interface import Interface


@implementer(ISerializeToJsonSummary)
@adapter(ICatalogBrain, Interface)
class PMBrainJSONSummarySerializer(DefaultJSONSummarySerializer):
    """ISerializeToJsonSummary adapter for brain."""

    def _extra_include(self, result):
        """ """
        return result

    def _additional_values(self, result):
        """ """
        return result

    @property
    def _additional_fields(self):
        """By default add 'UID' to returned data."""
        return ["id", "UID", "enabled"]

    def __call__(self):
        """ """
        result = super(PMBrainJSONSummarySerializer, self).__call__()

        # fullobjects for extra_includes?
        self.extra_include_fullobjects = False
        if "extra_include_fullobjects" in self.request.form:
            self.extra_include_fullobjects = True

        result = self._extra_include(result)
        result = self._additional_values(result)

        return result


@implementer(ISerializeToJsonSummary)
@adapter(IItem, Interface)
class PMJSONSummarySerializer(PMBrainJSONSummarySerializer):
    """ISerializeToJsonSummary adapter for object (not brain)."""
