# -*- coding: utf-8 -*-

from datetime import datetime
from plonemeeting.restapi.services.attendees import WRONG_ATTENDEE_TYPE
from plonemeeting.restapi.tests.base import BaseTestCase
from Products.CMFCore.permissions import View
from Products.PloneMeeting.browser.itemattendee import WRONG_POSITION_TYPE
from Products.PloneMeeting.tests.PloneMeetingTestCase import DEFAULT_USER_PASSWORD

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
        self.meeting = self.create("Meeting", date=datetime(2021, 9, 23, 10, 0))
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
        endpoint_url = "{0}/@attendees/{1}".format(
            self.portal_url, self.meeting_uid)
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
        endpoint_url = "{0}/@attendees/{1}".format(
            self.portal_url, self.item1_uid)
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

        # must be able to view the item to get attendees
        self.api_session.auth = ("pmCreator1", DEFAULT_USER_PASSWORD)
        self.changeUser("pmCreator1")
        self.assertTrue(self.hasPermission(View, self.item1))
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200, response.content)
        self.api_session.auth = ("pmCreator2", DEFAULT_USER_PASSWORD)
        self.changeUser("pmCreator2")
        self.assertFalse(self.hasPermission(View, self.item1))
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 400, response.content)

    def test_restapi_get_attendee_endpoint(self):
        """The @attendee GET on meeting and item."""
        # check response, especially order and attendee_type
        data = {
            self.meeting_uid: {
                # hp_uid: (attendee_type, signatory)
                self.hp1_uid: ('present', '1'),
                self.hp2_uid: ('excused', None),
                self.hp3_uid: ('present', None),
                self.hp4_uid: ('present', '2'), },
            self.item1_uid: {
                self.hp1_uid: ('present', '1'),
                self.hp2_uid: ('excused', None),
                self.hp3_uid: ('absent', None),
                self.hp4_uid: ('non_attendee', None), },
            self.item2_uid: {
                self.hp1_uid: ('present', '1'),
                self.hp2_uid: ('excused', None),
                self.hp3_uid: ('present', None),
                self.hp4_uid: ('present', '2'), }, }
        for url in (self.meeting_uid, self.item1_uid, self.item2_uid):
            for hp_uid in (self.hp1_uid, self.hp2_uid, self.hp3_uid, self.hp4_uid):
                endpoint_url = "{0}/@attendee/{1}/{2}".format(
                    self.portal_url, url, hp_uid)
                response = self.api_session.get(endpoint_url)
                json = response.json()
                self.assertEqual(json['position_type'],
                                 {u'title': u'D\xe9faut', u'token': u'default'})
                self.assertEqual(json['UID'], hp_uid)
                self.assertEqual(json['attendee_type']['token'], data[url][hp_uid][0])
                self.assertEqual(json['signatory'], data[url][hp_uid][1])

    def test_restapi_patch_meeting_attendee_endpoint(self):
        """The @attendee PATCH on meeting."""
        # test an attendee that is present
        self.assertTrue(self.hp1_uid in self.meeting.get_attendees())
        # set it absent
        json = {"attendee_type": "absent", }
        endpoint_url = "{0}/@attendee/{1}/{2}".format(
            self.portal_url, self.meeting_uid, self.hp1_uid)
        response = self.api_session.patch(endpoint_url, json=json)
        # this will generate an error because self.hp1_uid is signatory
        self.assertEqual(response.status_code, 500, response.content)
        self.assertEqual(
            response.json(),
            {u'message': u'can_not_remove_attendee_defined_as_signatory',
             u'type': u'Invalid'})
        # set self.hp1_uid no more signatory so it may be set absent
        self.assertEqual(self.meeting.get_signatories()[self.hp1_uid], '1')
        json = {"signatory": 0, }
        response = self.api_session.patch(endpoint_url, json=json)
        self.assertEqual(response.json()["attendee_type"],
                         {u'token': u'present', u'title': u'Present'})
        self.assertEqual(response.json()["signatory"], None)
        # this time self.hp1_uid me be set absent
        json = {"attendee_type": "absent", }
        response = self.api_session.patch(endpoint_url, json=json)
        self.assertEqual(response.json()["attendee_type"],
                         {u'token': u'absent', u'title': u'Absent'})
        # set it excused
        json = {"attendee_type": "excused", }
        response = self.api_session.patch(endpoint_url, json=json)
        self.assertEqual(response.json()["attendee_type"],
                         {u'token': u'excused', u'title': u'Absent (excused)'})
        # set it present
        json = {"attendee_type": "present", }
        response = self.api_session.patch(endpoint_url, json=json)
        self.assertEqual(response.json()["attendee_type"],
                         {u'token': u'present', u'title': u'Present'})
        # will raise Unauthorized if user not able to edit meeting
        self.api_session.auth = ("pmCreator1", DEFAULT_USER_PASSWORD)
        json = {"attendee_type": "absent", }
        response = self.api_session.patch(endpoint_url, json=json)
        self.assertEqual(response.status_code, 401, response.content)

    def test_restapi_patch_item_attendee_endpoint(self):
        """The @attendee PATCH on item."""
        # test an attendee that is excused on the meeting
        # not possible to change it's attendee_type on item
        self.assertTrue(self.hp2_uid in self.meeting.get_excused())
        # try to set it absent, will fail as not present on the meeting
        self.api_session.auth = ("pmManager", DEFAULT_USER_PASSWORD)
        json = {"attendee_type": "absent", }
        endpoint_url = "{0}/@attendee/{1}/{2}".format(
            self.portal_url, self.item1_uid, self.hp2_uid)
        response = self.api_session.patch(endpoint_url, json=json)
        self.assertEqual(response.status_code, 400, response.content)
        self.assertEqual(
            response.json(),
            {u'message': u'Can not set "Absent" a person that is not present on the meeting!\n',
             u'type': u'BadRequest'})
        # same for non_attendee
        json = {"attendee_type": "non_attendee", }
        response = self.api_session.patch(endpoint_url, json=json)
        self.assertEqual(response.status_code, 400, response.content)
        self.assertEqual(
            response.json(),
            {u'message': u'Can not set "Non attendee" a person that is not present on the meeting!\n',
             u'type': u'BadRequest'})
        # wrong attendee type
        json = {"attendee_type": "unknown", }
        response = self.api_session.patch(endpoint_url, json=json)
        self.assertEqual(response.status_code, 400, response.content)
        self.assertEqual(
            response.json(),
            {u'message': WRONG_ATTENDEE_TYPE % 'unknown', u'type': u'BadRequest'})
        # signatory
        # trying to set absent as signatory will not work
        self.assertTrue(self.hp2_uid in self.meeting.get_excused())
        json = {"signatory": 1}
        response = self.api_session.patch(endpoint_url, json=json)
        self.assertEqual(response.status_code, 400, response.content)
        self.assertEqual(
            response.json(),
            {u'message': u'Can not set "Signatory" a person that is not present on the meeting!\n',
             u'type': u'BadRequest'})
        # work with hp1_uid, already signatory on the meeting
        endpoint_url = "{0}/@attendee/{1}/{2}".format(
            self.portal_url, self.item1_uid, self.hp1_uid)
        self.assertTrue(self.hp1_uid in self.item1.get_item_signatories())
        # not able to set signatory for an item a user already signatory on the meeting
        response = self.api_session.patch(endpoint_url, json=json)
        self.assertEqual(response.status_code, 400, response.content)
        self.assertEqual(
            response.json(),
            {u'message': u'Can not set "Signatory" a person that is already signatory on the meeting!\n',
             u'type': u'BadRequest'})

        # now with self.hp3_uid that is not signatory on the meeting not on the item
        endpoint_url = "{0}/@attendee/{1}/{2}".format(
            self.portal_url, self.item1_uid, self.hp3_uid)
        self.assertFalse(self.hp3_uid in self.item1.get_item_signatories())
        self.assertFalse(self.hp3_uid in self.item1.get_item_signatories(real=True))
        json = {"signatory": 1}
        response = self.api_session.patch(endpoint_url, json=json)
        transaction.commit()
        self.assertEqual(response.json()['signatory'], '1')
        self.assertTrue(self.hp3_uid in self.item1.get_item_signatories())
        self.assertTrue(self.hp3_uid in self.item1.get_item_signatories(real=True))
        # need to remove and add signatory again to change a redefined signatory number
        json = {"signatory": 1}
        response = self.api_session.patch(endpoint_url, json=json)
        self.assertEqual(response.status_code, 400, response.content)
        self.assertEqual(
            response.json(),
            {u'message': u'Can not set "Signatory" a person already redefined as signatory on an item!\n',
             u'type': u'BadRequest'})
        json = {"signatory": 0}
        response = self.api_session.patch(endpoint_url, json=json)
        transaction.commit()
        self.assertIsNone(response.json()['signatory'])
        # trying to remove a non signatory will do nothing
        json = {"signatory": 0}
        response = self.api_session.patch(endpoint_url, json=json)
        self.assertEqual(response.status_code, 200, response.content)
        self.assertIsNone(response.json()['signatory'])
        # redefine signatory and position_type
        # wrong position_type
        json = {"signatory": 1, "position_type": 'unknown'}
        response = self.api_session.patch(endpoint_url, json=json)
        self.assertEqual(response.status_code, 400, response.content)
        self.assertEqual(
            response.json(),
            {u'message': WRONG_POSITION_TYPE % "unknown",
             u'type': u'BadRequest'})
        json = {"signatory": 2, "position_type": 'administrator'}
        response = self.api_session.patch(endpoint_url, json=json)
        # change signature_number and signatory position_type
        response_json = response.json()
        self.assertEqual(response_json['signatory'], u'2')
        self.assertEqual(response_json['signatory_position_type'],
                         {u'title': u'Administratrice',
                          u'token': u'administrator'})


def test_suite():
    from unittest import TestSuite, makeSuite

    suite = TestSuite()
    # add a prefix to avoid every PM tests to be executed
    suite.addTest(makeSuite(testServiceAttendees, prefix="test_restapi_"))
    return suite
