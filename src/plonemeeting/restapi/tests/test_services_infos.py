# -*- coding: utf-8 -*-

from plonemeeting.restapi.tests.base import BaseTestCase


class testServicePMInfos(BaseTestCase):
    """ """

    def tearDown(self):
        self.api_session.close()

    def test_restapi_infos_endpoint(self):
        """@infos"""
        endpoint_url = "{0}/@infos".format(self.portal_url)
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200)
        json = response.json()
        # return versions and connected_user
        self.assertTrue(u'Products.PloneMeeting' in json)
        self.assertTrue(u'plonemeeting.restapi' in json)
        self.assertTrue(u'imio.restapi' in json)
        self.assertEqual(json['connected_user'], u'pmManager')
        # when not connected
        self.api_session.auth = None
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200)
        json = response.json()
        # return versions and connected_user
        self.assertTrue(u'Products.PloneMeeting' in json)
        self.assertTrue(u'plonemeeting.restapi' in json)
        self.assertTrue(u'imio.restapi' in json)
        self.assertEqual(json['connected_user'], None)


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    # add a prefix to avoid every PM tests to be executed
    suite.addTest(makeSuite(testServicePMInfos, prefix='test_restapi_'))
    return suite
