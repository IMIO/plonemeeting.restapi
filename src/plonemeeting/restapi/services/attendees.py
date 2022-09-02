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
from plone.restapi.deserializer import json_body
from Products.PloneMeeting.utils import _itemNumber_to_storedItemNumber


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


@implementer(IPublishTraverse)
class AttendeePatch(Service):

    def __init__(self, context, request):
        super(AttendeePatch, self).__init__(context, request)
        self.attendee_uid = None

    def publishTraverse(self, request, name):
        if self.attendee_uid is None:
            self.attendee_uid = name
        else:
            raise NotFound(self, name, request)
        return self

    def reply(self):
        json = json_body(self.request)
        is_meeting = self.context.__class__.__name__ == "Meeting"
        meeting = self.context if is_meeting else self.context.getMeeting()
        if is_meeting:
            pass
        else:
            # MeetingItem
            attendee_type_mappings = {'present': '@@item_welcome_attendee_form',
                                      'absent': '@@item_byebye_attendee_form',
                                      'excused': '@@item_byebye_attendee_form',
                                      'non_attendee': '@@item_byebye_nonattendee_form'}

            attendee_type = json.get('attendee_type')
            form_name = attendee_type_mappings.get(attendee_type)
            if not form_name:
                raise Exception("Wrong attendee_type : \"%s\"" % attendee_type)
            form = self.context.restrictedTraverse(form_name)
            form.person_uid = self.attendee_uid
            form.not_present_type = attendee_type
            form.apply_until_item_number = _itemNumber_to_storedItemNumber(
                json.get('until_item_number', u'0'))
            form.meeting = meeting
            form._doApply()
            result = serialize_attendees(self.context, attendee_uid=self.attendee_uid)
            return result and result[0]
