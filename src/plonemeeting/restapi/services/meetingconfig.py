# -*- coding: utf-8 -*-

from plone import api
from plonemeeting.restapi.services.search import BaseSearchGet
from plonemeeting.restapi.config import CONFIG_ID_NOT_FOUND_ERROR
from zExceptions import BadRequest


class ConfigSearchGet(BaseSearchGet):
    """Returns a serialized content object.
    """

    def __init__(self, context, request):
        super(ConfigSearchGet, self).__init__(context, request)
        # we may ask for every configs by using config_id=*
        if self.config_id != "*":
            self.tool = api.portal.get_tool("portal_plonemeeting")
            self.cfg = self.tool.get(self.config_id, None)
            if not self.cfg:
                raise BadRequest(CONFIG_ID_NOT_FOUND_ERROR % self.config_id)

    @property
    def _type(self):
        # force to MeetingConfig
        return "MeetingConfig"

    def _set_query_before_hook(self):
        """ """
        query = super(ConfigSearchGet, self)._set_query_before_hook()
        query.pop('getConfigId')
        query['portal_type'] = self.type
        if self.config_id != "*":
            query['id'] = self.cfg.id
        else:
            query['sort_on'] = self.request.form.get('sort_on', 'getId')
        # by default only return active MeetingConfigs excepted if aksed
        if "review_state" not in query:
            query["review_state"] = "active"
        return query

    def reply(self):
        res = super(ConfigSearchGet, self).reply()
        if res["items"] and hasattr(self, "cfg"):
            # we asked for one single MeetingConfig, return it (not a list of result)
            res = res["items"][0]
        return res
