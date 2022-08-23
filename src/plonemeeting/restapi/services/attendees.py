# -*- coding: utf-8 -*-

from plone.restapi.interfaces import IExpandableElement
from plone.restapi.services import Service
from plonemeeting.restapi.serializer.base import serialize_attendees
from Products.PloneMeeting.interfaces import IMeetingContent
from zope.component import adapter
from zope.interface import implementer
from zope.interface import Interface
from zope.publisher.interfaces import IPublishTraverse
from zope.publisher.interfaces import NotFound


@implementer(IExpandableElement)
@adapter(IMeetingContent, Interface)
class Attendees(object):
    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self, expand=False):
        result = {"attendees": {"@id": "{}/@attendees".format(self.context.absolute_url())}}
        if not expand:
            return result

        # extend batch? DEFAULT_BATCH_SIZE = 25
        # self.request.form['b_size'] = 50

        result = serialize_attendees(self.context)
        return result


class AttendeesGet(Service):
    def reply(self):
        attendees = Attendees(self.context, self.request)
        return attendees(expand=True)


@implementer(IPublishTraverse)
class AttendeeGet(Service):

    def __init__(self, context, request):
        super(AttendeeGet, self).__init__(context, request)
        self.attendee_uid = None

    def publishTraverse(self, request, name):
        if self.attendee_uid is None:
            self.attendee_uid = name
        else:
            raise NotFound(self, name, request)
        return self

    def reply(self):
        result = serialize_attendees(self.context, attendee_uid=self.attendee_uid)
        return result and result[0]
