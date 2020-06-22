# -*- coding: utf-8 -*-

from plone import api
from plone.restapi.services.content.get import ContentGet
from plonemeeting.restapi.config import CONFIG_ID_ERROR
from plonemeeting.restapi.config import CONFIG_ID_NOT_FOUND_ERROR


class ConfigGet(ContentGet):
    """Returns a serialized content object.
    """

    def __init__(self, context, request):
        super(ConfigGet, self).__init__(context, request)
        self.tool = api.portal.get_tool("portal_plonemeeting")
        config_id = self._config_id
        self.cfg = self.tool.get(config_id, None)
        if not self.cfg:
            raise Exception(CONFIG_ID_NOT_FOUND_ERROR % config_id)

    @property
    def _config_id(self):
        if "config_id" not in self.request.form:
            raise Exception(CONFIG_ID_ERROR)
        return self.request.form.get("config_id")

    def reply(self):
        # set context to MeetingConfig
        self.context = self.cfg
        return super(ConfigGet, self).reply()
