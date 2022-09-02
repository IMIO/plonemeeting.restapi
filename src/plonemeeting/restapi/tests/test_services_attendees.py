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
        self.presentItem(self.item2)
        # setUp absent/excused on meeting and item
        self.hp1_uid = self.meeting.get_attendees()[0]
        self.hp2_uid = self.meeting.get_attendees()[1]
        self.hp3_uid = self.meeting.get_attendees()[2]
        self.hp4_uid = self.meeting.get_attendees()[3]
        self.meeting.ordered_contacts[self.hp2_uid]['attendee'] = False
        self.meeting.ordered_contacts[self.hp2_uid]['excused'] = True
        # absent on item
        self.meeting.item_absents[self.item1_uid] = [self.hp3_uid]
        # non_attendee on item
        self.meeting.item_non_attendees[self.item1_uid] = [self.hp4_uid]
        self.meeting._p_changed = True
        transaction.commit()

    def tearDown(self):
        self.api_session.close()
        transaction.abort()

    def test_restapi_get_attendees_endpoint(self):
        """The @attendees GET on meeting and item."""
        # check response, especially order and attendee_type
        # Meeting
        endpoint_url = "{0}/@attendees".format(self.meeting_url)
        response = self.api_session.get(endpoint_url)
        json = response.json()
        self.assertEqual(json[0]['UID'], self.hp1_uid)
        self.assertEqual(json[0]['attendee_type'], 'present')
        self.assertEqual(json[0]['signatory'], u'1')
        self.assertEqual(json[1]['UID'], self.hp2_uid)
        self.assertEqual(json[1]['attendee_type'], 'excused')
        self.assertEqual(json[1]['signatory'], None)
        self.assertEqual(json[2]['UID'], self.hp3_uid)
        self.assertEqual(json[2]['attendee_type'], 'present')
        self.assertEqual(json[2]['signatory'], None)
        self.assertEqual(json[3]['UID'], self.hp4_uid)
        self.assertEqual(json[3]['attendee_type'], 'present')
        self.assertEqual(json[3]['signatory'], u'2')
        # MeetingItem
        endpoint_url = "{0}/@attendees".format(self.item1_url)
        response = self.api_session.get(endpoint_url)
        json = response.json()
        self.assertEqual(json[0]['UID'], self.hp1_uid)
        self.assertEqual(json[0]['attendee_type'], 'present')
        self.assertEqual(json[0]['signatory'], u'1')
        self.assertEqual(json[1]['UID'], self.hp2_uid)
        self.assertEqual(json[1]['attendee_type'], 'excused')
        self.assertEqual(json[1]['signatory'], None)
        self.assertEqual(json[2]['UID'], self.hp3_uid)
        self.assertEqual(json[2]['attendee_type'], 'absent')
        self.assertEqual(json[2]['signatory'], None)
        self.assertEqual(json[3]['UID'], self.hp4_uid)
        self.assertEqual(json[3]['attendee_type'], 'non_attendee')
        # a non_attendee can not be signatory
        self.assertEqual(json[3]['signatory'], None)

    def test_restapi_get_attendee_endpoint(self):
        """The @attendee GET on meeting and item."""
        # check response, especially order and attendee_type
        data = {
            self.meeting_url: {
                # hp_uid: (attendee_type, signatory)
                self.hp1_uid: ('present', '1'),
                self.hp2_uid: ('excused', None),
                self.hp3_uid: ('present', None),
                self.hp4_uid: ('present', '2'), },
            self.item1_url: {
                self.hp1_uid: ('present', '1'),
                self.hp2_uid: ('excused', None),
                self.hp3_uid: ('absent', None),
                self.hp4_uid: ('non_attendee', None), },
            self.item2_url: {
                self.hp1_uid: ('present', '1'),
                self.hp2_uid: ('excused', None),
                self.hp3_uid: ('present', None),
                self.hp4_uid: ('present', '2'), }, }
        for url in (self.meeting_url, self.item1_url, self.item2_url):
            for hp_uid in (self.hp1_uid, self.hp2_uid, self.hp3_uid, self.hp4_uid):
                endpoint_url = "{0}/@attendee/{1}".format(url, hp_uid)
                response = self.api_session.get(endpoint_url)
                json = response.json()
                self.assertEqual(json['UID'], hp_uid)
                self.assertEqual(json['attendee_type'], data[url][hp_uid][0])
                self.assertEqual(json['signatory'], data[url][hp_uid][1])


def test_suite():
    from unittest import TestSuite, makeSuite

    suite = TestSuite()
    # add a prefix to avoid every PM tests to be executed
    suite.addTest(makeSuite(testServiceAttendees, prefix="test_restapi_"))
    return suite
