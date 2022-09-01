# -*- coding: utf-8 -*-

from DateTime import DateTime
from datetime import datetime
from plonemeeting.restapi.config import HAS_MEETING_DX
from plonemeeting.restapi.tests.base import BaseTestCase

import transaction


class testServiceAttendees(BaseTestCase):
    """GET/POST @attendees endpoints on item and meeting."""

    def setUp(self):
        """ """
        super(testServiceAttendees, self).setUp()
        self._setUpOrderedContacts()
        self.changeUser("pmManager")
        self.item1 = self.create("MeetingItem", proposingGroup=self.developers_uid)
        self.item1_uid = self.item1.UID()
        self.item1_url = self.item1.absolute_url()
        self.item2 = self.create("MeetingItem", proposingGroup=self.vendors_uid)
        self.item2_uid = self.item2.UID()
        self.item2_url = self.item2.absolute_url()
        if HAS_MEETING_DX:
            self.meeting = self.create("Meeting", date=datetime(2021, 9, 23, 10, 0))
        else:
            self.meeting = self.create("Meeting", date=DateTime('2021/09/23 10:0'))
        self.meeting_uid = self.meeting.UID()
        self.meeting_url = self.meeting.absolute_url()
        self.presentItem(self.item1)
        transaction.commit()

    def tearDown(self):
        self.api_session.close()
        transaction.abort()

    def test_restapi_get_attendees_item(self):
        """The @attendees GET on item."""
        # setUp absent/excused on meeting and item
        hp1_uid = self.meeting.get_attendees()[0]
        hp2_uid = self.meeting.get_attendees()[1]
        hp3_uid = self.meeting.get_attendees()[2]
        hp4_uid = self.meeting.get_attendees()[3]
        self.meeting.ordered_contacts[hp1_uid]['attendee'] = False
        self.meeting.ordered_contacts[hp1_uid]['absent'] = True
        self.meeting.ordered_contacts[hp2_uid]['attendee'] = False
        self.meeting.ordered_contacts[hp2_uid]['excused'] = True
        self.meeting.item_absents[self.item1_uid] = [hp3_uid]
        self.meeting._p_changed = True
        transaction.commit()

        # check response, especially order and attendee_type
        endpoint_url = "{0}/@attendees".format(self.item1_url)
        response = self.api_session.get(endpoint_url)
        json = response.json()
        self.assertEqual(json[0]['UID'], hp1_uid)
        self.assertEqual(json[0]['attendee_type'], 'absent')
        self.assertEqual(json[1]['UID'], hp2_uid)
        self.assertEqual(json[1]['attendee_type'], 'excused')
        self.assertEqual(json[2]['UID'], hp3_uid)
        self.assertEqual(json[2]['attendee_type'], 'absent')
        self.assertEqual(json[3]['UID'], hp4_uid)
        self.assertEqual(json[3]['attendee_type'], 'present')


def test_suite():
    from unittest import TestSuite, makeSuite

    suite = TestSuite()
    # add a prefix to avoid every PM tests to be executed
    suite.addTest(makeSuite(testServiceAttendees, prefix="test_restapi_"))
    return suite
