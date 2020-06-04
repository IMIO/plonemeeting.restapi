# -*- coding: utf-8 -*-

from plonemeeting.restapi.services.config import CONFIG_ID_ERROR
from plonemeeting.restapi.services.config import CONFIG_ID_NOT_FOUND_ERROR
from plonemeeting.restapi.tests.base import BaseTestCase

import transaction


class testServiceAdd(BaseTestCase):
    """@item POST endpoint"""

    def test_restapi_add_item_config_id_not_found(self):
        """ """
        endpoint_url = "{0}/@item".format(self.portal_url)
        response = self.api_session.post(
            endpoint_url,
            json={"config_id": "unknown"})
        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.json(),
            {u'message': CONFIG_ID_NOT_FOUND_ERROR % "unknown",
             u'type': u'Exception'})

    def test_restapi_add_item_required_params(self):
        """ """
        self.changeUser('pmManager')
        pmFolder = self.getMeetingFolder()
        self.assertEqual(len(pmFolder.objectIds('MeetingItem')), 0)
        endpoint_url = "{0}/@item".format(self.portal_url)
        response = self.api_session.post(endpoint_url)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json(),
                         {u'message': CONFIG_ID_ERROR,
                          u'type': u'Exception'})
        response = self.api_session.post(
            endpoint_url,
            json={"config_id": self.meetingConfig.getId(),
                  "proposingGroup": self.developers_uid,
                  "title": "My item"})
        self.assertEqual(response.status_code, 201)
        transaction.begin()
        pmFolder = self.getMeetingFolder()
        self.assertEqual(len(pmFolder.objectIds('MeetingItem')), 1)
        item = pmFolder.get('my-item')
        self.assertEqual(item.Title(), "My item")
        self.assertEqual(item.getProposingGroup(), self.developers_uid)


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    # add a prefix to avoid every PM tests to be executed
    suite.addTest(makeSuite(testServiceAdd, prefix='test_restapi_'))
    return suite
