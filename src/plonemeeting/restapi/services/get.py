# -*- coding: utf-8 -*-

from plone import api
from plonemeeting.restapi.config import CONFIG_ID_NOT_FOUND_ERROR
from plonemeeting.restapi.services.search import BaseSearchGet
from plonemeeting.restapi.utils import rest_uuid_to_object
from zExceptions import BadRequest


UID_REQUIRED_ERROR = 'The "UID or uid" parameter must be given!'
UID_WRONG_TYPE_ERROR = (
    "The element UID does not correspond to the type managed by this endpoint! "
    "Consider using @get endpoint or another specific endpoint!"
)


class UidSearchGet(BaseSearchGet):
    """Returns a serialized content object based on required UID parameter."""

    required_meta_type_id = None

    def __init__(self, context, request):
        super(UidSearchGet, self).__init__(context, request)
        self.external_id = self.request.form.get(
            "externalIdentifier",
            self.request.form.get("external_id"),
        )
        self.uid = self._uid
        self.config_id = self._config_id
        if self.config_id:
            self.tool = api.portal.get_tool("portal_plonemeeting")
            self.cfg = self.tool.get(self.config_id, None)
            if not self.cfg:
                raise BadRequest(CONFIG_ID_NOT_FOUND_ERROR % self.config_id)

    @property
    def _config_id(self):
        return super(UidSearchGet, self)._config_id

    @property
    def _uid(self):
        uid = self.request.form.get("UID") or self.request.form.get("uid")
        if not uid and not self.external_id:
            raise BadRequest(UID_REQUIRED_ERROR)
        return uid

    def _check_res_type(self, res):
        """ """
        if self.required_meta_type_id and res["items"]:
            # we have the portal_type in res, we need to get the meta_type
            # to compare it with self.required_meta_type_id
            portal_type = api.portal.get_tool("portal_types")[res["items"][0]["@type"]]
            # AT, meta_type is directly stored in content_meta_type
            if portal_type.__class__.__name__ == 'DynamicViewTypeInformation':
                meta_type = portal_type.content_meta_type
            else:
                # DX, klass is the dotted path the python klass
                meta_type = portal_type.klass.split('.')[-1]
            if self.required_meta_type_id != meta_type:
                raise BadRequest(UID_WRONG_TYPE_ERROR)

    def reply(self):
        """ """
        res = super(UidSearchGet, self).reply()
        self._check_res_type(res)
        if res["items"]:
            # we only have one single result
            res = res["items"][0]
        else:
            if self.uid:
                # will raise if element exist but inaccessible or not exist
                # do not try_restricted as it was just done in this endpoint
                rest_uuid_to_object(self.uid, try_restricted=False, in_name_of=self.in_name_of)
        return res


class ItemGet(UidSearchGet):
    """Get an item from it's UID, just check that returned value is a MeetingItem."""

    required_meta_type_id = "MeetingItem"


class MeetingGet(UidSearchGet):
    """Get a meeting from it's UID, just check that returned value is a Meeting."""

    required_meta_type_id = "Meeting"
