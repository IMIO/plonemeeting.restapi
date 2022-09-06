# -*- coding: utf-8 -*-

from imio.helpers.content import uuidToObject
from plone.restapi.deserializer import json_body
from plone.restapi.interfaces import IExpandableElement
from plone.restapi.services import Service
from plonemeeting.restapi.serializer.base import serialize_attendees
from Products.CMFPlone.utils import safe_unicode
from Products.PloneMeeting.content.meeting import _validate_attendees_removed_and_order
from Products.PloneMeeting.content.meeting import _validate_attendees_signatories
from Products.PloneMeeting.interfaces import IMeetingContent
from Products.PloneMeeting.utils import _itemNumber_to_storedItemNumber
from zope.component import adapter
from zope.i18n import translate
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

    def _manage_attendee_type(self, json, is_meeting, meeting):
        """Change attendee type on Meeting or MeetingItem.
           So a present is set absent, an absent is set excused, ..."""
        attendee_type_mappings = {'present': '@@item_welcome_attendee_form',
                                  'absent': '@@item_byebye_attendee_form',
                                  'excused': '@@item_byebye_attendee_form',
                                  'non_attendee': '@@item_byebye_nonattendee_form',
                                  'attendee': None}

        attendee_type = json.get('attendee_type')
        if attendee_type not in attendee_type_mappings:
            raise Exception("Wrong attendee_type : \"%s\"" % attendee_type)

        # Meeting
        if is_meeting:
            if attendee_type == 'present':
                attendee_type = 'attendee'
            # call validation
            all_meeting_attendees = self.context.get_all_attendees()
            meeting_attendees = list(all_meeting_attendees)
            if attendee_type != 'attendee':
                meeting_attendees.remove(self.attendee_uid)
            _validate_attendees_removed_and_order(
                self.context,
                meeting_attendees,
                all_meeting_attendees,
                self.context.get_signatories())
            self.context._update_attendee_type(
                self.attendee_uid, attendee_type, force_clear=True)
        else:
            # MeetingItem
            form_name = attendee_type_mappings.get(attendee_type)
            self.request.form['person_uid'] = safe_unicode(self.attendee_uid)
            form = self.context.restrictedTraverse(form_name)
            form.update()
            form.person_uid = self.attendee_uid
            form.not_present_type = attendee_type
            form.apply_until_item_number = _itemNumber_to_storedItemNumber(
                str(json.get('until_item_number', u'0')))
            form.meeting = meeting
            error = form._doApply()
            if error:
                # we get a message in error, translate it
                msg = translate(error, context=self.request)
                raise ValueError(msg)

    def _manage_signatory(self, json, is_meeting, meeting):
        """Manage signatories on Meeting and MeetingItem."""
        signature_number = json.get('signatory')
        if not isinstance(signature_number, int) or signature_number < 0 or signature_number > 20:
            raise Exception("Wrong signatory : \"%s\".  "
                            "An integer between 0 and 20 is required.  "
                            "Using 0 will unset signatory." % signature_number)
        signature_number = None if signature_number == 0 else safe_unicode(str(signature_number))
        # Meeting
        if is_meeting:
            # turn signature number integer into None or a unicode
            signature_numbers = self.context.get_signatories()
            signature_numbers.update({self.attendee_uid: signature_number})
            _validate_attendees_signatories(self.context, signature_numbers.values())
            self.context._update_signature_number(
                self.attendee_uid, signature_number or None)
        else:
            # MeetingItem
            self.request.form['person_uid'] = safe_unicode(self.attendee_uid)
            form_name = "@@item_redefine_signatory_form"
            if signature_number is None:
                form_name = "@@item_remove_redefined_signatory_form"
            form = self.context.restrictedTraverse(form_name)
            form.update()
            form.person_uid = self.attendee_uid
            if signature_number is not None:
                form.signature_number = signature_number
                # taken from json or left untouched
                position_type = json.get(
                    'position_type', uuidToObject(self.attendee_uid).position_type)
                form.position_type = position_type
            form.apply_until_item_number = _itemNumber_to_storedItemNumber(
                str(json.get('until_item_number', u'0')))
            form.meeting = meeting
            error = form._doApply()
            if error:
                # we get a message in error, translate it
                msg = translate(error, context=self.request)
                raise ValueError(msg)

    def reply(self):
        is_meeting = self.context.__class__.__name__ == "Meeting"
        meeting = self.context if is_meeting else self.context.getMeeting()
        json = json_body(self.request)
        was_managed = True
        if "attendee_type" in json:
            self._manage_attendee_type(json, is_meeting, meeting)
            was_managed = True
        if "signatory" in json:
            self._manage_signatory(json, is_meeting, meeting)
            was_managed = True

        result = None
        if was_managed:
            result = serialize_attendees(self.context, attendee_uid=self.attendee_uid)
        return result and result[0]
