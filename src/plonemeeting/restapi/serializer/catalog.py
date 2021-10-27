# -*- coding: utf-8 -*-

# XXX Override to query the serializer adapter with the real object
# XXX instead the catalog brain as we register different summary serializers.
# 2 things changed :
# - use LazyMap instead Lazy to be more specific
# - call summary serializer on object instead brain, check the XXX here under

from plone.restapi.batching import HypermediaBatch
from plone.restapi.interfaces import ISerializeToJson
from plone.restapi.interfaces import ISerializeToJsonSummary
from plone.restapi.serializer.catalog import LazyCatalogResultSerializer
from plonemeeting.restapi import logger
from Products.ZCatalog.Lazy import LazyMap
from zope.component import adapter
from zope.component import getMultiAdapter
from zope.interface import implementer
from zope.interface import Interface


log = logger


@implementer(ISerializeToJson)
# XXX register for LazyMap instead Lazy
@adapter(LazyMap, Interface)
class PMLazyCatalogResultSerializer(LazyCatalogResultSerializer):
    """ """

    def _use_own_summary_serializer(self, fullobjects):
        """Check if we need to use our own implementation of the summary serializer,
           necessary to manage additional_values and extra_include."""
        return bool(fullobjects or
                    self.request.form.get("extra_include", []) or
                    self.request.form.get("additional_values", []))

    def __call__(self, fullobjects=False):
        batch = HypermediaBatch(self.request, self.lazy_resultset)

        results = {}
        results["@id"] = batch.canonical_url
        results["items_total"] = batch.items_total
        links = batch.links
        if links:
            results["batching"] = links

        results["items"] = []
        use_own_summary = self._use_own_summary_serializer(fullobjects)
        for brain in batch:
            try:
                obj = use_own_summary and brain.getObject() or brain
            except AttributeError:
                # Guard in case the brain returned refers to an object that doesn't
                # exists because it failed to uncatalog itself or the catalog has
                # stale cataloged objects for some reason
                log.warning(
                    "Brain getObject error: {} doesn't exist anymore".format(
                        brain.getPath()
                    )
                )
                continue

            if fullobjects:
                result = getMultiAdapter(
                    (obj, self.request), ISerializeToJson
                )(include_items=False)
            else:
                result = getMultiAdapter(
                    (obj, self.request), ISerializeToJsonSummary
                )()

            results["items"].append(result)

        return results
