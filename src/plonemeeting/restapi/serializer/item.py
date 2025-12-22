# -*- coding: utf-8 -*-

from imio.helpers.content import uuidsToObjects
from plone import api
from plone.restapi.interfaces import ISerializeToJson
from plone.restapi.interfaces import ISerializeToJsonSummary
from plonemeeting.restapi.serializer.base import BaseATSerializeFolderToJson
from plonemeeting.restapi.serializer.base import serialize_attendees
from plonemeeting.restapi.serializer.base import serialize_extra_include_annexes
from plonemeeting.restapi.serializer.base import serialize_pod_templates
from plonemeeting.restapi.serializer.summary import PMBrainJSONSummarySerializer
from plonemeeting.restapi.utils import build_catalog_query
from Products.PloneMeeting.interfaces import IMeetingItem
from Products.PloneMeeting.utils import get_internal_number
from zope.component import adapter
from zope.interface import implementer
from zope.interface import Interface


class BaseSerializeItemToJson(object):
    """ """

    def _available_extra_includes(self, result):
        """ """
        result["@extra_includes"] = [
            "annexes",
            "attendees",
            "proposing_group",
            "category",
            "classifier",
            "groups_in_charge",
            "associated_groups",
            "pod_templates",
            "meeting",
            "linked_items",
            "*deliberation*",
            "config",
        ]
        return result

    def _extra_include_linked_items(self, result):
        """ """
        result["extra_include_linked_items"] = []
        # get the modes so we know which linked items to return
        modes = self.get_param('mode', ["auto"], extra_include_name="linked_items")
        linked_items = []
        for mode in modes:
            # every manually linked items
            if mode == "manual":
                linked_items += self.context.getManuallyLinkedItems(only_viewable=True)
            # every auto linked items, from first predecessor to last successor
            elif mode == "auto":
                # by default parameters include_successors=True, this will return
                # every auto linked items
                linked_items += self.context.get_predecessors(only_viewable=True)
            elif mode == "predecessor":
                predecessor = self.context.get_predecessor(unrestricted=False)
                if predecessor:
                    linked_items.append(predecessor)
            elif mode == "predecessors":
                linked_items += self.context.get_predecessors(
                    only_viewable=True, include_successors=False)
            elif mode == "successors":
                linked_items += self.context.get_successors(unrestricted=False)
            elif mode == "every_successors":
                linked_items += self.context.get_every_successors(unrestricted=False)
        query = build_catalog_query(self, extra_include_name="linked_items")
        if query:
            linked_item_uids = [linked_item.UID() for linked_item in linked_items]
            # we may unrestricted=True as we get linked items with unrestricted=False here above
            linked_items = uuidsToObjects(
                linked_item_uids, ordered=True, query=query, unrestricted=True)
        result["extra_include_linked_items"] = [
            self._get_serializer(linked_item, "linked_items")()
            for linked_item in linked_items]
        result["extra_include_linked_items_items_total"] = len(linked_items)
        return result

    def _extra_include(self, result):
        """To be simplified when moving MeetingItem to DX as extra_include name
           will be the same as attribute name defined in MeetingItem schema."""
        extra_include = self._get_asked_extra_include()
        if "proposing_group" in extra_include:
            proposing_group = self.context.getProposingGroup(theObject=True)
            result["extra_include_proposing_group"] = {}
            if proposing_group:
                serializer = self._get_serializer(proposing_group, "proposing_group")
                result["extra_include_proposing_group"] = serializer()
        if "category" in extra_include:
            category = self.context.getCategory(theObject=True, real=True)
            result["extra_include_category"] = {}
            if category:
                serializer = self._get_serializer(category, "category")
                result["extra_include_category"] = serializer()
        if "classifier" in extra_include:
            classifier = self.context.getClassifier(theObject=True)
            result["extra_include_classifier"] = {}
            if classifier:
                serializer = self._get_serializer(classifier, "classifier")
                result["extra_include_classifier"] = serializer()
        if "groups_in_charge" in extra_include:
            groups_in_charge = self.context.getGroupsInCharge(theObjects=True)
            result["extra_include_groups_in_charge"] = []
            for group_in_charge in groups_in_charge:
                serializer = self._get_serializer(group_in_charge, "groups_in_charge")
                result["extra_include_groups_in_charge"].append(serializer())
        if "associated_groups" in extra_include:
            associated_groups = self.context.getAssociatedGroups(theObjects=True)
            result["extra_include_associated_groups"] = []
            for associated_group in associated_groups:
                serializer = self._get_serializer(associated_group, "associated_groups")
                result["extra_include_associated_groups"].append(serializer())
        if "annexes" in extra_include:
            result = serialize_extra_include_annexes(result, self)
        if "pod_templates" in extra_include:
            result["extra_include_pod_templates"] = serialize_pod_templates(
                self.context, self)
        if "meeting" in extra_include:
            meeting = self.context.getMeeting()
            result["extra_include_meeting"] = {}
            if meeting:
                serializer = self._get_serializer(meeting, "meeting")
                result["extra_include_meeting"] = serializer()
        if "linked_items" in extra_include:
            result = self._extra_include_linked_items(result)
        if "config" in extra_include:
            tool = api.portal.get_tool('portal_plonemeeting')
            cfg = tool.getMeetingConfig(self.context)
            result["extra_include_config"] = {}
            if cfg:
                serializer = self._get_serializer(cfg, "config")
                result["extra_include_config"] = serializer()
        if "attendees" in extra_include:
            result["extra_include_attendees"] = serialize_attendees(
                self.context, extra_include_name="attendees", base_serializer=self)

        # various type of deliberation may be included
        # if we find a key containing "deliberation", we use it
        # add pass it to documentgenerator helper.deliberation_for_restapi
        delib_extra_includes = [ei for ei in extra_include
                                if "deliberation" in ei]
        if delib_extra_includes:
            # make the @@document-generation helper view available on self
            view = self.context.restrictedTraverse("document-generation")
            helper = view.get_generation_context_helper()
            deliberation = helper.deliberation_for_restapi(delib_extra_includes)
            result["extra_include_deliberation"] = deliberation

        return result

    def _additional_values(self, result, additional_values):
        """ """
        # add some formatted values
        if "*" in additional_values or "formatted_itemAssembly" in additional_values:
            result["formatted_itemAssembly"] = self.context.getItemAssembly(striked=True)
        if "*" in additional_values or "formatted_itemNumber" in additional_values:
            result["formatted_itemNumber"] = self.context.getItemNumber(for_display=True)

        # values including computed values
        # need to use "token/title" format
        # all_copyGroups
        if "*" in additional_values or "all_copyGroups" in additional_values:
            all_copyGroups = self.context.getAllCopyGroups(
                auto_real_plone_group_ids=True
            )
            vocab = self.context.getField('copyGroups').Vocabulary(self.context)
            all_copyGroups = [
                {"token": cg, "title": vocab.getValue(cg)}
                for cg in all_copyGroups]
            result["all_copyGroups"] = all_copyGroups
        # all_groupsInCharge
        # XXX to be removed when using PloneMeeting 4.2 as now
        # groupsInCharge are stored including "auto" groupsInCharge
        if "*" in additional_values or "all_groupsInCharge" in additional_values:
            all_groupsInCharge = self.context.getGroupsInCharge(includeAuto=True)
            vocab = self.context.getField('groupsInCharge').Vocabulary(self.context)
            all_groupsInCharge = [
                {"token": gic, "title": vocab.getValue(gic)}
                for gic in all_groupsInCharge]
            result["all_groupsInCharge"] = all_groupsInCharge
        return result


@implementer(ISerializeToJson)
@adapter(IMeetingItem, Interface)
class SerializeToJson(BaseSerializeItemToJson, BaseATSerializeFolderToJson):
    """ """

    def _include_fields(self, obj):
        """Manage internal_number manually as it is not a field for now but
           a stored attribute, will be a field when item will be DX."""
        result = super(SerializeToJson, self)._include_fields(obj)
        if self.fullobjects or "internal_number" in self.metadata_fields:
            result["internal_number"] = get_internal_number(obj)
        if self.fullobjects or "formatted_itemNumber" in self.metadata_fields:
            result["formatted_itemNumber"] = obj.getItemNumber(for_display=True)
        return result


@implementer(ISerializeToJsonSummary)
@adapter(IMeetingItem, Interface)
class SerializeToJsonSummary(BaseSerializeItemToJson, PMBrainJSONSummarySerializer):
    """ """
