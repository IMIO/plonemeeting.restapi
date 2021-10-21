# -*- coding: utf-8 -*-

from plonemeeting.restapi.tests.base import BaseTestCase


class testServicePMUsersGet(BaseTestCase):
    """ """

    def tearDown(self):
        self.api_session.close()

    def test_restapi_users_endpoint(self):
        """@users"""
        endpoint_url = "{0}/@users/pmManager".format(self.portal_url)
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200, response.content)
        json = response.json()
        self.assertEqual(json["username"], u'pmManager')
        self.assertEqual(json["email"], u'pmmanager@plonemeeting.org')
        self.assertFalse("groups" in json)
        # include_groups=true
        endpoint_url += "?include_groups=true"
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200, response.content)
        json = response.json()
        self.assertEqual(json["username"], u'pmManager')
        self.assertEqual(json["email"], u'pmmanager@plonemeeting.org')
        group_tokens = [group["token"] for group in json["groups"]]
        self.assertTrue(self.developers_creators in group_tokens)
        self.assertTrue(self.developers_creators in group_tokens)


def test_suite():
    from unittest import TestSuite, makeSuite

    suite = TestSuite()
    # add a prefix to avoid every PM tests to be executed
    suite.addTest(makeSuite(testServicePMUsersGet, prefix="test_restapi_"))
    return suite
