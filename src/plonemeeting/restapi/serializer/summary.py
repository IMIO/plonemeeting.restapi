# -*- coding: utf-8 -*-

from imio.restapi.serializer.base import DefaultJSONSummarySerializer
from OFS.interfaces import IItem
from plone.restapi.interfaces import ISerializeToJsonSummary
from plone.restapi.serializer.converters import json_compatible
from plone.restapi.serializer.summary import BLACKLISTED_ATTRIBUTES
from plone.restapi.serializer.summary import FIELD_ACCESSORS
from plonemeeting.restapi.serializer.base import ContentSerializeToJson
from Products.CMFCore.WorkflowCore import WorkflowException
from Products.ZCatalog.interfaces import ICatalogBrain
from zope.component import adapter
from zope.interface import implementer
from zope.interface import Interface


@implementer(ISerializeToJsonSummary)
@adapter(ICatalogBrain, Interface)
class PMBrainJSONSummarySerializer(DefaultJSONSummarySerializer, ContentSerializeToJson):
    """ISerializeToJsonSummary adapter for brain."""

    @property
    def _additional_fields(self):
        """By default add 'UID' to returned data."""
        return ["id", "UID", "enabled", "created", "modified"]

    def _get_metadata_fields_name(self):
        """May be overrided when necessary."""
        name = "metadata_fields"
        extra_include_name = getattr(self, "_extra_include_name", None)
        if extra_include_name is not None:
            name = "extra_include_{0}_metadata_fields".format(extra_include_name)
        return name

    def _init(self):
        """ """
        self.metadata_fields = []
        self.asked_extra_include = []
        self.asked_additional_values = []
        self.asked_includes = []
        self.fullobjects = False

    def __call__(self):
        """ """
        # result = super(PMBrainJSONSummarySerializer, self).__call__()
        # Override to not use a IContentListingObject as we have the object!
        summary = {}
        for field in self.metadata_fields():
            if field.startswith("_") or field in BLACKLISTED_ATTRIBUTES:
                continue
            accessor = FIELD_ACCESSORS.get(field, field)
            value = getattr(self.context, accessor, None)
            try:
                if callable(value):
                    value = value()
            except WorkflowException:
                summary[field] = None
                continue
            summary[field] = json_compatible(value)

        # call _init so elements like self.fullobjects are initialized
        self._init()

        summary = self._after__call__(self.context, summary)
        return summary


@implementer(ISerializeToJsonSummary)
@adapter(IItem, Interface)
class PMJSONSummarySerializer(PMBrainJSONSummarySerializer):
    """ISerializeToJsonSummary adapter for object (not brain)."""
