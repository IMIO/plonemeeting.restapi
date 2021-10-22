# -*- coding: utf-8 -*-

from imio.helpers.content import uuidsToObjects
from plone import api
from plone.restapi.services.content.get import ContentGet
from zExceptions import BadRequest


UID_REQUIRED_ERROR = 'The "UID or uid" parameter must be given!'
UID_NOT_FOUND_ERROR = 'No element found with UID "%s"!'
UID_NOT_ACCESSIBLE_ERROR = (
    'Element with UID "%s" was found but user "%s" can not access it!'
)
UID_WRONG_TYPE_ERROR = (
    "The element UID does not correspond to the type managed by this endpoint! "
    "Consider using @get endpoint or another specific endpoint!"
)


class UidGet(ContentGet):
    """Returns a serialized content object based on required UID parameter."""

    def __init__(self, context, request):
        super(UidGet, self).__init__(context, request)
        self.uid = self._uid

    @property
    def _uid(self):
        if "UID" not in self.request.form and "uid" not in self.request.form:
            raise Exception(UID_REQUIRED_ERROR)
        return self.request.form.get("UID") or self.request.form.get("uid")

    def _check_obj(self):
        """ """
        return

    def reply(self):
        # change self.context with element found with self.uid
        objs = uuidsToObjects(uuids=self.uid)
        if not objs:
            # try to get it unrestricted
            objs = uuidsToObjects(uuids=self.uid, unrestricted=True)
            if objs:
                raise BadRequest(
                    UID_NOT_ACCESSIBLE_ERROR
                    % (self.uid, api.user.get_current().getId())
                )
            else:
                raise BadRequest(UID_NOT_FOUND_ERROR % self.uid)

        self.context = objs[0]
        self._check_obj()
        # set include_items=False by default in request
        if not self.request.form.get("include_items", None):
            self.request.form["include_items"] = False
        return super(UidGet, self).reply()


class ItemGet(UidGet):
    """Get an item from it's UID, just check that returned value is a MeetingItem."""

    def _check_obj(self):
        """ """
        if not self.context.__class__.__name__ == "MeetingItem":
            raise BadRequest(UID_WRONG_TYPE_ERROR)


class MeetingGet(UidGet):
    """Get a meeting from it's UID, just check that returned value is a Meeting."""

    def _check_obj(self):
        """ """
        if not self.context.__class__.__name__ == "Meeting":
            raise BadRequest(UID_WRONG_TYPE_ERROR)
