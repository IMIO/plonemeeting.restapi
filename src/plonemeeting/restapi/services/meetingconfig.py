# -*- coding: utf-8 -*-

from plone import api
from plone.restapi.interfaces import ISerializeToJson
from plone.restapi.interfaces import ISerializeToJsonSummary
from plone.restapi.services import Service
from plonemeeting.restapi.config import CONFIG_ID_ERROR
from plonemeeting.restapi.config import CONFIG_ID_NOT_FOUND_ERROR
from zope.component import queryMultiAdapter


class ConfigGet(Service):
    """Returns a serialized content object.
    """

    def __init__(self, context, request):
        super(ConfigGet, self).__init__(context, request)
        self.tool = api.portal.get_tool("portal_plonemeeting")
        config_id = self._config_id
        self.cfg = self.tool.get(config_id, None)
        if not self.cfg:
            raise Exception(CONFIG_ID_NOT_FOUND_ERROR % config_id)
        # fullobjects for MeetingConfig?
        self.fullobjects = False
        if "fullobjects" in self.request.form:
            self.fullobjects = True

    @property
    def _config_id(self):
        if "config_id" not in self.request.form:
            raise Exception(CONFIG_ID_ERROR)
        return self.request.form.get("config_id")

    def reply(self):
        # set context to MeetingConfig
        self.context = self.cfg

        if self.fullobjects:
            serializer = queryMultiAdapter((self.context, self.request), ISerializeToJson)
        else:
            serializer = queryMultiAdapter((self.context, self.request), ISerializeToJsonSummary)

        if serializer is None:
            self.request.response.setStatus(501)
            return dict(error=dict(message="No serializer available."))

        return serializer()
