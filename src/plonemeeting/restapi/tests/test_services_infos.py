# -*- coding: utf-8 -*-

from plone import api
from plone.app.testing import login
from plone.app.testing import logout
from plone.app.testing import TEST_USER_NAME
from plone.app.testing import TEST_USER_PASSWORD
from plonemeeting.restapi.tests.base import BaseTestCase

import requests
import transaction


class testServicePMInfos(BaseTestCase):
    """ """

    def tearDown(self):
        self.api_session.close()

    def test_restapi_infos_endpoint(self):
        """@infos"""
        endpoint_url = "{0}/@infos".format(self.portal_url)
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200, response.content)
        json = response.json()
        # return versions and connected_user
        self.assertTrue(u"Products.PloneMeeting" in json["packages"])
        self.assertTrue(u"plonemeeting.restapi" in json["packages"])
        self.assertTrue(u"imio.restapi" in json["packages"])
        self.assertEqual(json["connected_user"], u"pmManager")

        # when not connected
        self.api_session.auth = None
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200, response.content)
        json = response.json()
        # return versions and connected_user
        self.assertTrue(u"Products.PloneMeeting" in json["packages"])
        self.assertTrue(u"plonemeeting.restapi" in json["packages"])
        self.assertTrue(u"imio.restapi" in json["packages"])
        self.assertEqual(json["connected_user"], None)

    def test_restapi_infos_stats(self):
        """@infos stats"""
        endpoint_url = "{0}/@infos?include_stats=1".format(self.portal_url)
        # only available to Manager
        api.user.grant_roles(TEST_USER_NAME, roles=["Manager"])
        logout()
        login(self.portal, TEST_USER_NAME)
        transaction.commit()
        # stats contains various data
        response = requests.get(
            endpoint_url,
            headers={"Accept": "application/json"},
            auth=(TEST_USER_NAME, TEST_USER_PASSWORD),
        )
        self.assertEqual(response.status_code, 200, response.content)
        json = response.json()
        self.assertTrue(u"Meeting" in json["stats"][u"types"])
        self.assertTrue(u"MeetingItem" in json["stats"][u"types"])
        self.assertTrue(u"annex" in json["stats"][u"types"])
        self.assertTrue(u"annexDecision" in json["stats"][u"types"])
        self.assertEqual(json["stats"][u"types"]["MeetingConfig"], 2)


def test_suite():
    from unittest import TestSuite, makeSuite

    suite = TestSuite()
    # add a prefix to avoid every PM tests to be executed
    suite.addTest(makeSuite(testServicePMInfos, prefix="test_restapi_"))
    return suite
