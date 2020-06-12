# -*- coding: utf-8 -*-

from plonemeeting.restapi.services.get import UID_NOT_ACCESSIBLE_ERROR
from plonemeeting.restapi.services.get import UID_NOT_FOUND_ERROR
from plonemeeting.restapi.services.get import UID_REQUIRED_ERROR
from plonemeeting.restapi.services.get import UID_WRONG_TYPE_ERROR
from plonemeeting.restapi.tests.base import BaseTestCase
from Products.PloneMeeting.tests.PloneMeetingTestCase import DEFAULT_USER_PASSWORD

import transaction


class testServiceGetUid(BaseTestCase):
    """@get endpoint, let's get element based on UID."""

    def setUp(self):
        """ """
        super(testServiceGetUid, self).setUp()
        self.changeUser('pmManager')
        self.item1 = self.create('MeetingItem', proposingGroup=self.developers_uid)
        self.item1_uid = self.item1.UID()
        self.item2 = self.create('MeetingItem', proposingGroup=self.vendors_uid)
        self.item2_uid = self.item2.UID()
        transaction.commit()

    def tearDown(self):
        self.api_session.close()
        transaction.abort()

    def test_restapi_get_uid_required(self):
        """The 'UID' or 'uid' parameter must be given"""
        endpoint_url = "{0}/@get".format(self.portal_url)
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json(),
                         {u'message': UID_REQUIRED_ERROR,
                          u'type': u'Exception'})
        endpoint_url += '?UID={0}'.format(self.item1.UID())
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200)

    def test_restapi_get_uid_not_found(self):
        """When given UID does not exist"""
        endpoint_url = "{0}/@get?UID=unknown".format(self.portal_url)
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.json(),
                         {u'message': UID_NOT_FOUND_ERROR % "unknown",
                          u'type': u'BadRequest'})

    def test_restapi_get_uid_not_accessible(self):
        """When given UID exists but current user can not access it"""
        endpoint_url = "{0}/@get?UID={1}".format(self.portal_url, self.item2_uid)
        # pmCreator1 can not access item with proposingGroup 'vendors'
        self.api_session.auth = ('pmCreator1', DEFAULT_USER_PASSWORD)
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.json(),
                         {u'message': UID_NOT_ACCESSIBLE_ERROR % (self.item2_uid, "pmCreator1"),
                          u'type': u'BadRequest'})

    def _check_get_uid_endpoint(self, endpoint_name='@get'):
        """ """
        endpoint_url = "{0}/{1}?UID={2}".format(self.portal_url, endpoint_name, self.item1_uid)
        response = self.api_session.get(endpoint_url)
        json = response.json()
        self.assertEqual(json['id'], self.item1.getId())
        self.assertEqual(json['UID'], self.item1_uid)
        # by default, no items
        self.assertFalse("items" in json)

    def test_restapi_get_uid(self):
        """When given UID is accessible, it is returned"""
        self._check_get_uid_endpoint()

    def test_restapi_get_uid_item(self):
        """There is a @item convenience endpoint that is just a shortcut to @get"""
        self._check_get_uid_endpoint(endpoint_name="@item")

    def test_restapi_get_uid_item_wrong_type(self):
        """@item endpoint is supposed to return an item, so if we receive an UID
           of another type, we raise"""
        endpoint_url = "{0}/@item?UID={1}".format(self.portal_url,
                                                  self.portal.Members.pmManager.UID())
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.json(),
                         {u'message': UID_WRONG_TYPE_ERROR,
                          u'type': u'BadRequest'})


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    # add a prefix to avoid every PM tests to be executed
    suite.addTest(makeSuite(testServiceGetUid, prefix='test_restapi_'))
    return suite
