# -*- coding: utf-8 -*-

from imio.helpers.content import base_hasattr
from imio.restapi.serializer.base import DefaultJSONSummarySerializer
from OFS.interfaces import IItem
from plone.restapi.interfaces import ISerializeToJsonSummary
from plonemeeting.restapi.serializer.base import ContentSerializeToJson
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
        """Add some defaults."""
        res = super(PMBrainJSONSummarySerializer, self)._additional_fields
        return res + ["enabled", "created", "modified"]

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

    def _include_custom(self, obj, result):
        """Custom related to PloneMeeting:
           - organization: include "full_id" by default."""
        from plonemeeting.restapi.serializer.organization import org_full_id
        # serializer may be initialized with an object and not a brain
        if base_hasattr(obj, 'getObject'):
            obj = obj.getObject()
        if obj.portal_type == "organization":
            result['full_id'] = org_full_id(obj)
        return result

    def __call__(self):
        """ """
        result = super(PMBrainJSONSummarySerializer, self).__call__()

        # call _init so elements like self.fullobjects are initialized
        self._init()

        result = self._after__call__(self.context, result)
        return result


@implementer(ISerializeToJsonSummary)
@adapter(IItem, Interface)
class PMJSONSummarySerializer(PMBrainJSONSummarySerializer):
    """ISerializeToJsonSummary adapter for object (not brain)."""
