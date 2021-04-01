# -*- coding: utf-8 -*-

from imio.restapi.utils import listify
from plone.restapi.interfaces import ISerializeToJson
from plonemeeting.restapi.serializer.base import BaseATSerializeToJson
from Products.PloneMeeting.interfaces import IMeetingItem
from zope.component import adapter
from zope.component import queryMultiAdapter
from zope.interface import implementer
from zope.interface import Interface


@implementer(ISerializeToJson)
@adapter(IMeetingItem, Interface)
class SerializeToJson(BaseATSerializeToJson):
    """ """

    def _extra_include(self, result):
        """ """
        extra_include = listify(self.request.form.get("extra_include", []))
        if "category" in extra_include:
            category = self.context.getCategory(theObject=True, real=True)
            result["extra_include_category"] = {}
            if category:
                serializer = queryMultiAdapter(
                    (category, self.request), ISerializeToJson
                )
                result["extra_include_category"] = serializer()
        if "proposingGroup" in extra_include:
            proposingGroup = self.context.getProposingGroup(theObject=True)
            result["extra_include_proposingGroup"] = {}
            if proposingGroup:
                serializer = queryMultiAdapter(
                    (proposingGroup, self.request), ISerializeToJson
                )
                result["extra_include_proposingGroup"] = serializer()
        if "meeting" in extra_include:
            meeting = self.context.getMeeting()
            result["extra_include_meeting"] = {}
            if meeting:
                serializer = queryMultiAdapter(
                    (meeting, self.request), ISerializeToJson
                )
                result["extra_include_meeting"] = serializer(include_items=False)
        delib_extra_includes = [ei for ei in extra_include
                                if "deliberation" in ei]
        if delib_extra_includes:
            # make the @@document-generation helper view available on self
            view = self.context.restrictedTraverse("document-generation")
            helper = view.get_generation_context_helper()
            deliberation = helper.deliberation_for_restapi(delib_extra_includes)
            result["extra_include_deliberation"] = deliberation

        return result

    def _additional_values(self, result):
        """ """
        # add some formatted values
        result["formatted_itemAssembly"] = self.context.getItemAssembly(striked=True)
        result["formatted_itemNumber"] = self.context.getItemNumber(for_display=True)
        # values including computed values
        result["all_copyGroups"] = self.context.getAllCopyGroups(
            auto_real_plone_group_ids=True
        )
        result["all_groupsInCharge"] = self.context.getGroupsInCharge(includeAuto=True)
        return result
