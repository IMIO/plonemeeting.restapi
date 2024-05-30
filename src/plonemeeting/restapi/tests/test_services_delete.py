# -*- coding: utf-8 -*-

from imio.helpers.content import object_values
from plonemeeting.restapi.testing import PM_REST_TEST_ADD_PROFILE_FUNCTIONAL
from plonemeeting.restapi.tests.base import BaseTestCase
from Products.PloneMeeting.tests.PloneMeetingTestCase import DEFAULT_USER_PASSWORD

import transaction


class testServiceDelete(BaseTestCase):
    """DELETE method."""

    layer = PM_REST_TEST_ADD_PROFILE_FUNCTIONAL

    def tearDown(self):
        self.api_session.close()
        transaction.abort()

    def test_restapi_delete_item(self):
        """Delete an item."""
        self.changeUser("pmCreator1")
        item = self.create("MeetingItem")
        validated_item = self.create("MeetingItem")
        self.validateItem(validated_item)
        transaction.commit()
        folder = item.getParentNode()
        self.assertTrue(item in folder.objectValues())
        self.assertTrue(validated_item in folder.objectValues())
        self.api_session.auth = ("pmCreator1", DEFAULT_USER_PASSWORD)
        response = self.api_session.delete(item.absolute_url())
        self.assertEqual(response.status_code, 204, response.content)
        validated_response = self.api_session.delete(validated_item.absolute_url())
        self.assertEqual(validated_response.status_code, 401, response.content)
        transaction.commit()
        self.assertFalse(item in folder.objectValues())
        self.assertTrue(validated_item in folder.objectValues())

    def test_restapi_delete_meeting(self):
        """Delete a meeting."""
        cfg = self.meetingConfig
        self._removeConfigObjectsFor(cfg)
        self.changeUser("pmManager")
        empty_meeting = self.create("Meeting")
        closed_meeting = self.create("Meeting")
        self.closeMeeting(closed_meeting)
        self.assertEqual(closed_meeting.query_state(), "closed")
        meeting = self._createMeetingWithItems()
        transaction.commit()
        folder = empty_meeting.getParentNode()
        self.assertTrue(empty_meeting in folder.objectValues())
        # meeting with items
        self.assertTrue(meeting in folder.objectValues())
        self.assertTrue(object_values(folder, "MeetingItem"))
        # trying to delete a meeting that is not empty will raise Unauthorized
        response = self.api_session.delete(meeting.absolute_url())
        self.assertEqual(response.status_code, 401, response.content)
        # but deleting an empty meeting is ok
        response = self.api_session.delete(empty_meeting.absolute_url())
        self.assertEqual(response.status_code, 204, response.content)
        # deleting a closed meeting will raise Unauthorized
        response = self.api_session.delete(closed_meeting.absolute_url())
        self.assertEqual(response.status_code, 401, response.content)
        transaction.commit()
        self.assertFalse(empty_meeting in folder.objectValues())
        self.assertTrue(closed_meeting in folder.objectValues())
        self.assertTrue(meeting in folder.objectValues())
        self.assertTrue(object_values(folder, "MeetingItem"))
        # a Manager may delete a meeting and it's items
        self.api_session.auth = ("siteadmin", DEFAULT_USER_PASSWORD)
        response = self.api_session.delete(meeting.absolute_url())
        self.assertEqual(response.status_code, 204, response.content)
        response = self.api_session.delete(closed_meeting.absolute_url())
        self.assertEqual(response.status_code, 204, response.content)
        transaction.commit()
        self.assertFalse(closed_meeting in folder.objectValues())
        self.assertFalse(meeting in folder.objectValues())
        self.assertFalse(object_values(folder, "MeetingItem"))

    def test_restapi_delete_annex(self):
        """Delete an annex."""
        self.changeUser("pmCreator1")
        item = self.create("MeetingItem")
        item_annex = self.addAnnex(item)
        validated_item = self.create("MeetingItem")
        validated_item_annex = self.addAnnex(validated_item)
        self.validateItem(validated_item)
        self.changeUser('pmManager')
        meeting = self.create('Meeting')
        meeting_annex = self.addAnnex(meeting)
        closed_meeting = self.create('Meeting')
        closed_meeting_annex = self.addAnnex(closed_meeting)
        self.closeMeeting(closed_meeting)
        transaction.commit()
        # annex on meeting not removable by "pmCreator1"
        self.api_session.auth = ("pmCreator1", DEFAULT_USER_PASSWORD)
        response = self.api_session.delete(meeting_annex.absolute_url())
        self.assertEqual(response.status_code, 401, response.content)
        # may be removed by "pmManager"
        self.api_session.auth = ("pmManager", DEFAULT_USER_PASSWORD)
        response = self.api_session.delete(meeting_annex.absolute_url())
        self.assertEqual(response.status_code, 204, response.content)
        response = self.api_session.delete(closed_meeting_annex.absolute_url())
        self.assertEqual(response.status_code, 401, response.content)
        # remove annex on item
        self.api_session.auth = ("pmCreator1", DEFAULT_USER_PASSWORD)
        response = self.api_session.delete(item_annex.absolute_url())
        self.assertEqual(response.status_code, 204, response.content)
        response = self.api_session.delete(validated_item_annex.absolute_url())
        self.assertEqual(response.status_code, 401, response.content)
        # annex on validated item removable by "pmManager"
        self.api_session.auth = ("pmManager", DEFAULT_USER_PASSWORD)
        response = self.api_session.delete(validated_item_annex.absolute_url())
        self.assertEqual(response.status_code, 204, response.content)


def test_suite():
    from unittest import TestSuite, makeSuite

    suite = TestSuite()
    # add a prefix to avoid every PM tests to be executed
    suite.addTest(makeSuite(testServiceDelete, prefix="test_restapi_"))
    return suite
