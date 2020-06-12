# -*- coding: utf-8 -*-

from plonemeeting.restapi.config import CONFIG_ID_ERROR
from plonemeeting.restapi.config import CONFIG_ID_NOT_FOUND_ERROR
from plonemeeting.restapi.tests.base import BaseTestCase

import transaction


class testServiceConfig(BaseTestCase):
    """ """

    def tearDown(self):
        self.api_session.close()

    def test_restapi_config_required_params(self):
        """ """
        endpoint_url = "{0}/@search".format(self.portal_url)
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json(),
                         {u'message': CONFIG_ID_ERROR,
                          u'type': u'Exception'})
        endpoint_url += '?config_id={0}'.format(self.meetingConfig.getId())
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200)

    def test_restapi_config_config_id_not_found(self):
        """ """
        endpoint_url = "{0}/@search?config_id=unknown".format(self.portal_url)
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.json(),
            {u'message': CONFIG_ID_NOT_FOUND_ERROR % "unknown",
             u'type': u'Exception'})

    def test_restapi_config_endpoint(self):
        """@config"""
        cfg = self.meetingConfig
        cfgId = cfg.getId()
        endpoint_url = "{0}/@config?config_id={1}".format(self.portal_url, cfgId)
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200)
        json = response.json()
        # by default, no "items"
        self.assertFalse("items" in json)
        self.assertEqual(json['id'], cfgId)
        self.assertEqual(json['UID'], cfg.UID())

    def test_restapi_config_extra_include_categories(self):
        """@config"""
        cfg = self.meetingConfig
        cfg.setUseGroupsAsCategories(False)
        cfgId = cfg.getId()
        transaction.commit()
        # categories
        endpoint_url_pattern = "{0}/@config?config_id={1}&extra_include={2}"
        endpoint_url = endpoint_url_pattern.format(
            self.portal_url, cfgId, "categories")
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200)
        json = response.json()
        categories = json['extra_include_categories']
        self.assertEqual(categories[0]['id'], u'development')
        self.assertEqual(categories[0]['@type'], u'MeetingCategory')

    def test_restapi_config_extra_include_pod_templates(self):
        """@config"""
        cfg = self.meetingConfig
        cfgId = cfg.getId()
        endpoint_url_pattern = "{0}/@config?config_id={1}&extra_include={2}"
        endpoint_url = endpoint_url_pattern.format(
            self.portal_url, cfgId, "pod_templates")
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200)
        json = response.json()
        pod_templates = json['extra_include_pod_templates']
        self.assertEqual(pod_templates[0]['id'], u'styles1')
        self.assertEqual(pod_templates[0]['@type'], u'StyleTemplate')
        self.assertEqual(pod_templates[4]['id'], u'itemTemplate')
        self.assertEqual(pod_templates[4]['@type'], u'ConfigurablePODTemplate')

    def test_restapi_config_extra_include_searches(self):
        """@config extra_include=searches"""
        cfg = self.meetingConfig
        cfgId = cfg.getId()
        endpoint_url_pattern = "{0}/@config?config_id={1}&extra_include={2}"
        endpoint_url = endpoint_url_pattern.format(
            self.portal_url, cfgId, "searches")
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200)
        json = response.json()
        searches = json['extra_include_searches']
        self.assertEqual(searches[0]['id'], u'searchmyitems')
        self.assertEqual(searches[0]['@type'], u'DashboardCollection')


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    # add a prefix to avoid every PM tests to be executed
    suite.addTest(makeSuite(testServiceConfig, prefix='test_restapi_'))
    return suite
