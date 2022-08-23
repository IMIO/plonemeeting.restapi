# -*- coding: utf-8 -*-

from Acquisition import aq_inner
from Acquisition import aq_parent
from collective.documentgenerator.interfaces import IGenerablePODTemplates
from collective.iconifiedcategory.utils import _categorized_elements
from collective.iconifiedcategory.utils import get_categorized_elements
from imio.helpers.content import base_hasattr
from imio.helpers.content import get_vocab
from imio.restapi.serializer.base import SerializeFolderToJson as IMIODXSerializeFolderToJson
from imio.restapi.serializer.base import SerializeToJson as IMIODXSerializeToJson
from plone import api
from plone.autoform.interfaces import READ_PERMISSIONS_KEY
from plone.dexterity.interfaces import IDexterityContainer
from plone.dexterity.interfaces import IDexterityContent
from plone.dexterity.utils import iterSchemata
from plone.restapi.batching import HypermediaBatch
from plone.restapi.deserializer import boolean_value
from plone.restapi.interfaces import IFieldSerializer
from plone.restapi.interfaces import IObjectPrimaryFieldTarget
from plone.restapi.interfaces import ISerializeToJson
from plone.restapi.interfaces import ISerializeToJsonSummary
from plone.restapi.serializer.atcontent import SerializeFolderToJson as ATSerializeFolderToJson
from plone.restapi.serializer.converters import json_compatible
from plone.restapi.serializer.expansion import expandable_elements
from plone.restapi.serializer.nextprev import NextPrevious
from plone.supermodel.utils import mergedTaggedValueDict
from plonemeeting.restapi import logger
from plonemeeting.restapi.config import ANNEXES_FILTER_VALUES
from plonemeeting.restapi.interfaces import IPMRestapiLayer
from plonemeeting.restapi.utils import get_param
from plonemeeting.restapi.utils import get_serializer
from Products.CMFCore.utils import getToolByName
from zope.component import adapter
from zope.component import ComponentLookupError
from zope.component import getAdapter
from zope.component import getMultiAdapter
from zope.component import queryMultiAdapter
from zope.interface import implementer
from zope.interface import Interface
from zope.schema import getFields


NO_VOCAB_ERROR = "Trying to get vocabulary for field %s but it is None"
SUFFIXED_CHOICES_PATTERN = "%s__choices"


def serialize_pod_templates(context, serializer):
    """Serialize generable POD templates for p_context."""
    # get generatable POD template for self.context
    adapter = getAdapter(context, IGenerablePODTemplates)
    generable_templates = adapter.get_generable_templates()
    result = []
    for pod_template in generable_templates:
        pod_serializer = serializer._get_serializer(pod_template, "pod_templates")
        # to be used to compute url to generate element
        pod_serializer.original_context = context
        result.append(pod_serializer())
    return result


def _get_annex_uids(data, filters):
    """Compatibility for PM4.1.x/4.2.x, as filters can not be passed to
       get_categorized_elements, we manage it manually.
       So we compute uids to keep and we pass it to get_categorized_elements.
       XXX to be removed when using 4.2.x+ for everybody."""
    uids = []
    for annex_uid, annex_infos in data.items():
        # check filters
        keep = True
        for k, v in filters.items():
            if annex_infos[k] != v:
                keep = False
                break
        if keep:
            uids.append(annex_uid)
    return uids


def serialize_annexes(context, filters, extra_include_name=None, base_serializer=None):
    """Serialize visible annexes regarding filters found in request."""
    result = []
    # can not use parameter filters due to compatibility 4.1.x, use uids instead
    # XXX to be adapted, just pass filters to get_categorized_elements and
    # remove uids computation
    uids = _get_annex_uids(_categorized_elements(context), filters)
    # uids must contains something or passing an empty list means do not filter on uids
    uids = uids or ["dummy_uid"]
    annexes = get_categorized_elements(
        context, result_type="objects", uids=uids)  # , filters=filters)
    for annex in annexes:
        serializer = get_serializer(
            annex, extra_include_name=extra_include_name, serializer=base_serializer)
        result.append(serializer())
    return result


def serialize_attendees(context, attendee_uid=None, extra_include_name=None, base_serializer=None):
    """ """
    result = []
    meeting = context.__class__.__name__ == "Meeting" and context or context.getMeeting()
    attendee_types = {}
    attendee_types.update({attendee_uid: 'present' for attendee_uid in meeting.get_attendees()})
    attendee_types.update({absent_uid: 'absent' for absent_uid in meeting.get_absents()})
    attendee_types.update({excused_uid: 'excused' for excused_uid in meeting.get_excused()})
    voters = meeting.get_voters()
    for attendee in context.get_all_attendees(the_objects=True):
        if attendee_uid is not None and attendee.UID() != attendee_uid:
            continue
        serializer = get_serializer(
            attendee, extra_include_name=extra_include_name, serializer=base_serializer)
        serialized = serializer()
        # manage "attendee_type"
        serialized["attendee_type"] = attendee_types[serialized['UID']]
        # manage "voter"
        serialized["voter"] = serialized['UID'] in voters
        result.append(serialized)
    return result


def serialize_person(held_position, serializer):
    """ """

    return {}


def serialize_extra_include_annexes(result, serializer):
    """ """
    # compute filters to get annexes
    filters = {}
    for filter_value in ANNEXES_FILTER_VALUES:
        value = serializer.get_param(
            filter_value,
            default=None,
            extra_include_name="annexes")
        if value is not None:
            filters[filter_value] = boolean_value(value)
    result["extra_include_annexes"] = serialize_annexes(
        serializer.context, filters, "annexes", serializer)
    return result


def serialize_extra_include_attendees(result, serializer):
    """ """
    return result


class BaseSerializeToJson(object):
    """__call__ must be redefined by class heritating from BaseSerializeToJson."""

    def _init(self):
        """ """
        self.metadata_fields = self.get_param('metadata_fields', [])
        self.asked_extra_include = self._get_asked_extra_include()
        self.asked_additional_values = self._get_asked_additional_values()
        self.asked_includes = self._get_asked_includes()
        # fullobjects is True:
        # if actually asked in request
        # or if nothing else asked
        self.fullobjects = boolean_value(self.get_param('fullobjects', False)) or \
            (not self.metadata_fields and
             not self.asked_extra_include and
             not self.asked_additional_values and
             not self.asked_includes)

    def _get_workflow_state(self, obj):
        wftool = api.portal.get_tool("portal_workflow")
        review_state = wftool.getInfoFor(obj, name="review_state", default=None)
        return review_state

    def _available_includes(self):
        """Internal function to determinate what are the available include_... values."""
        return [v.lstrip('_') for v in dir(self) if v.startswith('_include_')]

    def _available_extra_includes(self, result):
        """ """
        result["@extra_includes"] = []
        return result

    def _get_asked_extra_include(self):
        """ """
        extra_include = self.get_param("extra_include", [])
        # filter on _available_extra_includes this make we do not forget
        # to add an extra_include to _available_extra_includes
        aeis = self._available_extra_includes({})["@extra_includes"]
        filtered_extra_include = [
            ei for ei in extra_include if ei in aeis]
        # handle available extra_include starting with *
        starting_available_extra_include = tuple(
            aei[1:] for aei in aeis if aei.startswith('*'))
        # handle available extra_include ending with *
        ending_available_extra_include = tuple(
            aei[:-1] for aei in aeis if aei.endswith('*'))
        # handle available extra_include containing something
        containing_available_extra_include = tuple(
            aei[1:-1] for aei in aeis
            if aei.endswith('*') and aei.startswith('*'))
        if starting_available_extra_include or \
           ending_available_extra_include or \
           containing_available_extra_include:
            filtered_extra_include += [
                ei for ei in extra_include
                if ei.startswith(starting_available_extra_include) or
                ei.endswith(ending_available_extra_include) or
                [caei for caei in containing_available_extra_include if caei in ei]]
        return filtered_extra_include

    def _extra_include(self, result):
        """ """
        return result

    def _get_asked_additional_values(self):
        """ """
        # when fullobjects, additional_values default is ["*"]
        # otherwise additional_values default is []
        # self.fullobjects is still not computed
        if boolean_value(self.get_param("fullobjects", False)) is True:
            additional_values = self.get_param("additional_values", ["*"])
        else:
            additional_values = self.get_param("additional_values", [])
        return additional_values

    def _get_asked_includes(self):
        """ """
        return [v for v in self._available_includes()
                if self.get_param(v, None) is not None]

    def _additional_values(self, result, additional_values):
        """ """
        return result

    def _include_custom(self, obj, result):
        """Custom part made to be overrided when necessary."""
        return {}

    def _after__call__(self, obj, result):
        """ """
        # Include custom
        result.update(self._include_custom(obj, result))

        # only call _extra_include if relevant
        result = self._available_extra_includes(result)
        if self.get_param("extra_include", []):
            result = self._extra_include(result)

        # complete with additional values if relevant
        if self.asked_additional_values:
            result = self._additional_values(result, self.asked_additional_values)

        return result

    def _get_serializer(self, obj, extra_include_name):
        """ """
        return get_serializer(obj,
                              extra_include_name,
                              serializer=self)

    def get_param(self, value, default=False, extra_include_name=None):
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

        if self.get_param("include_base_data", True):
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
            }
            # add "enabled" if it exists
            if base_hasattr(obj, "enabled"):
                result["enabled"] = obj.enabled
        return result

    def _include_nextprev(self, obj):
        """ """
        result = {}
        if self.fullobjects or self.get_param('include_nextprev'):
            nextprevious = NextPrevious(obj)
            result.update(
                {"previous_item": nextprevious.previous, "next_item": nextprevious.next}
            )
        return result

    def _include_parent(self, obj):
        """ """
        result = {}
        # parent is only included when specifically asked, even when fullobjects
        if self.get_param('include_parent', False):
            parent = aq_parent(aq_inner(obj))
            parent_summary = getMultiAdapter(
                (parent, self.request), ISerializeToJsonSummary
            )()
            result["parent"] = parent_summary
        return result

    def _include_components(self, obj):
        """ """
        result = {}
        if self.fullobjects or self.get_param('include_components'):
            result.update(expandable_elements(self.context, self.request))
        return result

    def _include_fields(self, obj):
        """ """
        raise NotImplementedError

    def _include_choices_for(self, obj):
        """ """
        raise NotImplementedError

    def _include_items(self, obj, include_items):
        """ """
        result = {}
        include_items = self.get_param("include_items", include_items)
        if include_items:
            query = self._build_query()

            catalog = getToolByName(self.context, "portal_catalog")
            brains = catalog(query)

            batch = HypermediaBatch(self.request, brains)

            result["items_total"] = batch.items_total
            if batch.links:
                result["batching"] = batch.links

            if self.fullobjects:
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
        if self.fullobjects or self.get_param('include_target_url'):
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
        if self.fullobjects or self.get_param('include_allow_discussion'):
            result["allow_discussion"] = getMultiAdapter(
                (self.context, self.request), name="conversation_view"
            ).enabled()
        return result

    def _include_layout(self, obj):
        """ """
        result = {}
        if self.fullobjects or self.get_param('include_layout'):
            result["layout"] = self.context.getLayout()
        return result

    def getVersion(self, version):
        """ """
        return self.context

    def __call__(self, version=None, include_items=False):
        """Change include_items=False by default.
           Override to manage a way to get only what we want :
           - fullobjects, by default this will make element behave like in plone.restapi;
           - include_parent=False, to include the "parent" in the result;
           - include_nextprev=False, to include next/prev information;
           - include_components=True, to include @components (expandables);
           - metadata_fields=[], when given, this will only return selected values.
           """
        version = "current" if version is None else version
        obj = self.getVersion(version)
        self._init()

        # Include base_data
        result = self._include_base_data(obj)

        # Include parent
        result.update(self._include_parent(obj))

        # Include next/prev information
        result.update(self._include_nextprev(obj))

        # Include expandable elements (@components)
        result.update(self._include_components(obj))

        # Include metadata_fields
        result.update(self._include_fields(obj))

        # Include vocabulary values
        result.update(self._include_choices_for(obj))

        # Include items
        result.update(self._include_items(obj, include_items))

        # Include targetUrl
        result.update(self._include_target_url(obj))

        # Include allow_discussion
        result.update(self._include_allow_discussion(obj))

        # Include layout
        result.update(self._include_layout(obj))

        # call _after__call__ that manages additional_values and extra_includes
        result = self._after__call__(obj, result)
        return result


@implementer(ISerializeToJson)
@adapter(Interface, Interface)
class BaseATSerializeFolderToJson(ContentSerializeToJson, ATSerializeFolderToJson):
    """ """

    def _get_readable_fields(self, obj, field_names=[]):
        """ """
        fields = []
        for field in obj.Schema().fields():
            field_name = field.getName()
            if field_names and field_name not in field_names:
                continue
            if "r" not in field.mode or not field.checkPermission(
                "r", obj
            ):  # noqa: E501
                continue
            fields.append((field_name, field))
        return fields

    def _include_choices_for(self, obj):
        """ """
        result = {}
        choices_for = self.get_param('include_choices_for', [])
        if choices_for:
            for field_name, field in self._get_readable_fields(
                    obj, field_names=choices_for):
                if not field.vocabulary and not field.vocabulary_factory:
                    logger.warning(NO_VOCAB_ERROR % field_name)
                    continue
                vocab = field.Vocabulary(obj)
                data_name = SUFFIXED_CHOICES_PATTERN % field_name
                result[data_name] = []
                for term_id, term_title in vocab.items():
                    if term_id not in ['', '_none_']:
                        result[data_name].append(
                            {'token': term_id, 'title': term_title})
        return result

    def _include_fields(self, obj):
        """ """
        result = {}
        # Compute fields if fullobjects or metadata_fields
        if self.fullobjects or self.metadata_fields:
            for field_name, field in self._get_readable_fields(
                    obj, field_names=self.metadata_fields or []):
                serializer = queryMultiAdapter(
                    (field, self.context, self.request), IFieldSerializer
                )
                if serializer is not None:
                    result[field_name] = serializer()
        return result


@implementer(ISerializeToJson)
@adapter(IDexterityContent, IPMRestapiLayer)
class BaseDXSerializeToJson(ContentSerializeToJson, IMIODXSerializeToJson):
    """ """

    def _get_readable_fields(self, obj, field_names=[]):
        """ """
        fields = []
        for schema in iterSchemata(self.context):
            read_permissions = mergedTaggedValueDict(schema, READ_PERMISSIONS_KEY)
            for field_name, field in getFields(schema).items():
                if field_names and field_name not in field_names:
                    continue
                if not self.check_permission(read_permissions.get(field_name), obj):
                    continue
                fields.append((field_name, field))
        return fields

    def _include_choices_for(self, obj):
        """ """
        result = {}
        choices_for = self.get_param('include_choices_for', [])
        if choices_for:
            for field_name, field in self._get_readable_fields(
                    obj, field_names=choices_for):
                if base_hasattr(field, "value_type"):
                    vocab_name = field.value_type.vocabularyName
                else:
                    vocab_name = field.vocabularyName
                if vocab_name is None:
                    logger.warning(NO_VOCAB_ERROR % field_name)
                    continue
                vocab = get_vocab(obj, vocab_name)
                data_name = SUFFIXED_CHOICES_PATTERN % field_name
                result[data_name] = []
                for term in vocab._terms:
                    serializer = getMultiAdapter(
                        (term, self.request), interface=ISerializeToJson)
                    result[data_name].append(serializer())
        return result

    def _include_fields(self, obj):
        """ """
        result = {}
        # Compute fields if fullobjects or metadata_fields
        if self.fullobjects or self.metadata_fields:
            for field_name, field in self._get_readable_fields(
                    obj, field_names=self.metadata_fields or []):
                # serialize the field
                serializer = queryMultiAdapter(
                    (field, obj, self.request), IFieldSerializer
                )
                value = serializer()
                result[json_compatible(field_name)] = value

        return result


@implementer(ISerializeToJson)
@adapter(IDexterityContainer, IPMRestapiLayer)
class BaseDXSerializeFolderToJson(BaseDXSerializeToJson, IMIODXSerializeFolderToJson):
    """ """
