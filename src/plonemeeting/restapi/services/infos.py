# -*- coding: utf-8 -*-

from imio.restapi.services.infos import InfosGet
from plone import api
from Products.PloneMeeting.utils import getAdvicePortalTypeIds


class PMInfosGet(InfosGet):
    """ """

    def _stats_types_queries(self):
        queries = {}
        tool = api.portal.get_tool("portal_plonemeeting")
        # types MeetingConfig
        mConfigs = tool.getActiveConfigs(check_using_groups=False)
        queries["MeetingConfig"] = {
            "portal_type": "MeetingConfig",
            "review_state": "active",
        }
        meeting_types = [cfg.getMeetingTypeName() for cfg in mConfigs]
        # types Meeting
        queries["Meeting"] = {"portal_type": meeting_types}
        item_types = [cfg.getItemTypeName() for cfg in mConfigs]
        # types MeetingItem
        queries["MeetingItem"] = {"portal_type": item_types}
        # types annex
        queries["annex"] = {"portal_type": "annex"}
        # types annexDecision
        queries["annexDecision"] = {"portal_type": "annexDecision"}
        # types advices (meetingadvice, meetingadvicefinances, ...)
        for advice_type in getAdvicePortalTypeIds():
            queries[advice_type] = {"portal_type": advice_type}
        return queries

    def _packages_names(self):
        """To be overrided !!!
           Returns list of package names."""
        return ["imio.restapi", "Products.PloneMeeting", "plonemeeting.restapi"]
