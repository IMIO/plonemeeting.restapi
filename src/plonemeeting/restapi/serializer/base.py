# -*- coding: utf-8 -*-

from Acquisition import aq_base
from Acquisition import aq_inner
from Acquisition import aq_parent
from imio.restapi.serializer.base import SerializeFolderToJson as IMIODXSerializeFolderToJson
from imio.restapi.serializer.base import SerializeToJson as IMIODXSerializeToJson
from imio.restapi.utils import listify
from plone.autoform.interfaces import READ_PERMISSIONS_KEY
from plone.dexterity.interfaces import IDexterityContainer
from plone.dexterity.interfaces import IDexterityContent
from plone.dexterity.utils import iterSchemata
from plone.restapi.batching import HypermediaBatch
from plone.restapi.interfaces import IFieldSerializer
from plone.restapi.interfaces import IObjectPrimaryFieldTarget
from plone.restapi.interfaces import ISerializeToJson
from plone.restapi.interfaces import ISerializeToJsonSummary
from plone.restapi.serializer.atcontent import SerializeFolderToJson as ATSerializeFolderToJson
from plone.restapi.serializer.converters import json_compatible
from plone.restapi.serializer.expansion import expandable_elements
from plone.restapi.serializer.nextprev import NextPrevious
from plone.supermodel.utils import mergedTaggedValueDict
from plonemeeting.restapi.interfaces import IPMRestapiLayer
from plonemeeting.restapi.utils import get_param
from plonemeeting.restapi.utils import get_serializer
from Products.CMFCore.utils import getToolByName
from zope.component import adapter
from zope.component import ComponentLookupError
from zope.component import getMultiAdapter
from zope.component import queryMultiAdapter
from zope.interface import implementer
from zope.interface import Interface
from zope.schema import getFields


class BaseSerializeToJson(object):
    """__call__ must be redefined by class heritating from BaseSerializeToJson."""

    def _additional_values(self, result, additional_values):
        """ """
        return result

    def _after__call__(self, result):
        """ """
        # only call _extra_include if relevant
        if self._get_param("extra_include", []):
            result = self._extra_include(result)

        # when fullobjects, additional_values default is ["*"] except if include_all=False
        # otherwise additional_values default is []
        if self._get_param("fullobjects", False) and self._get_param("include_all", True):
            additional_values = self._get_param("additional_values", ["*"])
        else:
            additional_values = self._get_param("additional_values", [])
        if additional_values:
            result = self._additional_values(result, additional_values)

        return result

    def _get_serializer(self, obj, extra_include_name):
        """ """
        return get_serializer(obj,
                              extra_include_name,
                              serializer=self)

    def _get_param(self, value, default=False, extra_include_name=None):
        """ """
        return get_param(value,
                         default=default,
                         extra_include_name=extra_include_name,
                         serializer=self)


class ContentSerializeToJson(BaseSerializeToJson):
    """ """

    def _include_base_data(self, obj):
        """ """
        result = {}
        if self._get_param("include_base_data", True):
            result = {
                # '@context': 'http://www.w3.org/ns/hydra/context.jsonld',
                "@id": obj.absolute_url(),
                "id": obj.id,
                "@type": obj.portal_type,
                "created": json_compatible(obj.created()),
                "modified": json_compatible(obj.modified()),
                "review_state": self._get_workflow_state(obj),
                "UID": obj.UID(),
                "title": obj.Title(),
                "is_folderish": bool(getattr(aq_base(obj), 'isPrincipiaFolderish', False)),
            }
        return result

    def _include_nextprev(self, obj):
        """ """
        result = {}
        if self.include_all or self._get_param('include_nextprev'):
            nextprevious = NextPrevious(obj)
            result.update(
                {"previous_item": nextprevious.previous, "next_item": nextprevious.next}
            )
        return result

    def _include_parent(self, obj):
        """ """
        result = {}
        if self.include_all or self._get_param('include_parent'):
            parent = aq_parent(aq_inner(obj))
            parent_summary = getMultiAdapter(
                (parent, self.request), ISerializeToJsonSummary
            )()
            result["parent"] = parent_summary
        return result

    def _include_components(self, obj):
        """ """
        result = {}
        if self.include_all or self._get_param('include_components'):
            result.update(expandable_elements(self.context, self.request))
        return result

    def _include_fields(self, obj):
        """ """
        raise NotImplementedError

    def _include_items(self, obj, include_items):
        """ """
        result = {}
        include_items = self._get_param("include_items", include_items)
        if include_items:
            query = self._build_query()

            catalog = getToolByName(self.context, "portal_catalog")
            brains = catalog(query)

            batch = HypermediaBatch(self.request, brains)

            result["items_total"] = batch.items_total
            if batch.links:
                result["batching"] = batch.links

            if "fullobjects" in list(self.request.form):
                result["items"] = getMultiAdapter(
                    (brains, self.request), ISerializeToJson
                )(fullobjects=True)["items"]
            else:
                result["items"] = [
                    getMultiAdapter((brain, self.request), ISerializeToJsonSummary)()
                    for brain in batch
                ]
        return result

    def _include_target_url(self, obj):
        """ """
        result = {}
        if self.include_all or self._get_param('include_target_url'):
            target_url = None
            try:
                target_url = getMultiAdapter(
                    (self.context, self.request), IObjectPrimaryFieldTarget
                )()
            except ComponentLookupError:
                # only available on DX content
                pass
            if target_url:
                result["targetUrl"] = target_url
        return result

    def _include_allow_discussion(self, obj):
        """ """
        result = {}
        if self.include_all or self._get_param('include_allow_discussion'):
            result["allow_discussion"] = getMultiAdapter(
                (self.context, self.request), name="conversation_view"
            ).enabled()
        return result

    def _include_layout(self, obj):
        """ """
        result = {}
        if self.include_all or self._get_param('include_layout'):
            result["layout"] = self.context.getLayout()
        return result

    def _include_custom(self, obj, result):
        """Custom part made to be overrided when necessary."""
        return {}

    def __call__(self, version=None, include_items=False):
        """Change include_items=False by default.
           Override to manage a way to get only what we want :
           - include_all=True, by default this will make element behave like in plone.restapi;
           - include_default=True, when include_all=False, only return a limited number of metadata;
           - include_parent=False, to include the "parent" in the result;
           - include_nextprev=False, to include next/prev information;
           - include_components=True, to include @components (expandables);
           - metadata_fields=[], when given, this will only return selected values.
           """
        version = "current" if version is None else version
        obj = self.getVersion(version)

        self.metadata_fields = listify(self._get_param('metadata_fields', []))
        # Include all
        # False if given or if metadata_fields are given
        self.include_all = self._get_param('include_all', True)

        # Include base_data
        result = self._include_base_data(obj)

        # Include parent
        result.update(self._include_parent(obj))

        # Include next/prev information
        result.update(self._include_nextprev(obj))

        # Include expandable elements (@components)
        result.update(self._include_components(obj))

        # Include metadta_fields
        result.update(self._include_fields(obj))

        # Include items
        result.update(self._include_items(obj, include_items))

        # Include targetUrl
        result.update(self._include_target_url(obj))

        # Include allow_discussion
        result.update(self._include_allow_discussion(obj))

        # Include layout
        result.update(self._include_layout(obj))

        # Include custom
        result.update(self._include_custom(obj, result))

        # call _after__call__ that manages additional_values and extra_includes
        result = self._after__call__(result)
        return result


@implementer(ISerializeToJson)
@adapter(Interface, Interface)
class BaseATSerializeFolderToJson(ContentSerializeToJson, ATSerializeFolderToJson):
    """ """

    def _include_fields(self, obj):
        """ """
        result = {}
        # Compute fields if include_all or metadata_fields
        if self.include_all or self.metadata_fields:

            for field in obj.Schema().fields():

                name = field.getName()
                # only keep relevant fields
                if (self.include_all and not self.metadata_fields) or name in self.metadata_fields:
                    if "r" not in field.mode or not field.checkPermission(
                        "r", obj
                    ):  # noqa: E501
                        continue

                    serializer = queryMultiAdapter(
                        (field, self.context, self.request), IFieldSerializer
                    )
                    if serializer is not None:
                        result[name] = serializer()
        return result


@implementer(ISerializeToJson)
@adapter(IDexterityContent, IPMRestapiLayer)
class BaseDXSerializeToJson(ContentSerializeToJson, IMIODXSerializeToJson):
    """ """

    def _include_fields(self, obj):
        """ """
        result = {}
        # Compute fields if include_all or metadata_fields
        if self.include_all or self.metadata_fields:
            for schema in iterSchemata(self.context):
                read_permissions = mergedTaggedValueDict(schema, READ_PERMISSIONS_KEY)

                for name, field in getFields(schema).items():

                    # only keep relevant fields
                    if (self.include_all and not self.metadata_fields) or name in self.metadata_fields:

                        if not self.check_permission(read_permissions.get(name), obj):
                            continue

                        # serialize the field
                        serializer = queryMultiAdapter(
                            (field, obj, self.request), IFieldSerializer
                        )
                        value = serializer()
                        result[json_compatible(name)] = value

        return result


@implementer(ISerializeToJson)
@adapter(IDexterityContainer, IPMRestapiLayer)
class BaseDXSerializeFolderToJson(ContentSerializeToJson, IMIODXSerializeFolderToJson):
    """ """
