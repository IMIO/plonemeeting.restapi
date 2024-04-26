# -*- coding: utf-8 -*-

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
        item = self.create('MeetingItem')
        validated_item = self.create('MeetingItem')
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


def test_suite():
    from unittest import TestSuite, makeSuite

    suite = TestSuite()
    # add a prefix to avoid every PM tests to be executed
    suite.addTest(makeSuite(testServiceDelete, prefix="test_restapi_"))
    return suite
