# -*- coding: utf-8 -*-

from plone.restapi.interfaces import ISerializeToJson
from plonemeeting.restapi.serializer.base import BaseATSerializeToJson
from plonemeeting.restapi.utils import listify
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
        if "deliberation" in extra_include:
            # make the @@document-generation helper view available on self
            view = self.context.restrictedTraverse("document-generation")
            helper = view.get_generation_context_helper()
            # the method helper.output_for_restapi manage what is returned by this endpoint
            deliberation = helper.output_for_restapi()
            result["extra_include_deliberation"] = deliberation

        return result

    def _additional_values(self, result):
        """ """
        # add some formatted values
        result["formatted_itemAssembly"] = self.context.displayStrikedItemAssembly()
        result["formatted_itemNumber"] = self.context.getItemNumber(for_display=True)
        # values including computed values
        result["all_copyGroups"] = self.context.getAllCopyGroups(
            auto_real_plone_group_ids=True
        )
        result["all_groupsInCharge"] = self.context.getGroupsInCharge(includeAuto=True)
        return result
