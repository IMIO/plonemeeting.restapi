# -*- coding: utf-8 -*-

from plonemeeting.restapi.tests.base import BaseTestCase
from Products.PloneMeeting.tests.PloneMeetingTestCase import DEFAULT_USER_PASSWORD

import transaction


class testServicePMUsersGet(BaseTestCase):
    """ """

    def setUp(self):
        super(testServicePMUsersGet, self).setUp()
        # restrict self.meetingConfig access to developers
        self.meetingConfig.setUsingGroups([self.developers_uid])
        transaction.commit()

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
        # accessible as Manager
        self.api_session.auth = ("siteadmin", DEFAULT_USER_PASSWORD)
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200, response.content)
        json = response.json()
        self.assertEqual(json["username"], u'pmManager')
        self.assertEqual(json["email"], u'pmmanager@plonemeeting.org')

    def test_restapi_users_groups(self):
        """@users?extra_include=groups"""
        endpoint_url = "{0}/@users/pmManager?extra_include=groups".format(
            self.portal_url)
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200, response.content)
        json = response.json()
        self.assertEqual(json["username"], u'pmManager')
        # extra_include=groups will return organizations of the user (any suffixes)
        self.assertEqual(len(json["extra_include_groups"]), 2)
        org_uids = [org["UID"] for org in json["extra_include_groups"]]
        self.assertTrue(self.developers_uid in org_uids)
        self.assertTrue(self.vendors_uid in org_uids)
        # get only orgs using "creators" suffix
        endpoint_url += "&extra_include_groups_suffixes=creators"
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200, response.content)
        json = response.json()
        self.assertEqual(len(json["extra_include_groups"]), 1)
        self.assertEqual(json["extra_include_groups"][0]["UID"], self.developers_uid)

    def test_restapi_users_configs(self):
        """@users?extra_include=app_groups"""
        cfg1_id = self.meetingConfig.getId()
        cfg2_id = self.meetingConfig2.getId()
        endpoint_url = "{0}/@users/pmManager?extra_include=configs".format(
            self.portal_url)
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200, response.content)
        json = response.json()
        self.assertEqual(json["username"], u'pmManager')
        # extra_include=configs will return MeetingConfigs the user may access
        self.assertEqual(len(json["extra_include_configs"]), 2)
        cfg_ids = [cfg["id"] for cfg in json["extra_include_configs"]]
        self.assertEqual(sorted(cfg_ids), sorted([cfg1_id, cfg2_id]))
        # check for pmCreator2 that does not have access to cfg1
        endpoint_url = "{0}/@users/pmCreator2?extra_include=configs".format(self.portal_url)
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200, response.content)
        json = response.json()
        self.assertEqual(len(json["extra_include_configs"]), 1)
        self.assertEqual(json["extra_include_configs"][0]["id"], cfg2_id)

    def test_restapi_users_app_groups(self):
        """@users?extra_include=app_groups"""
        endpoint_url = "{0}/@users/pmManager?extra_include=app_groups".format(
            self.portal_url)
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200, response.content)
        json = response.json()
        self.assertEqual(json["username"], u'pmManager')
        # extra_include=app_groups will return Plone groups
        group_tokens = [group["token"] for group in json["extra_include_app_groups"]]
        self.assertTrue(self.developers_creators in group_tokens)
        self.assertTrue(self.developers_creators in group_tokens)

    def test_restapi_users_categories(self):
        """@users?extra_include=categories"""
        cfg = self.meetingConfig
        cfg_id = cfg.getId()
        cfg2 = self.meetingConfig2
        cfg2_id = cfg2.getId()
        endpoint_url = "{0}/@users/pmManager?extra_include=categories".format(
            self.portal_url)
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200, response.content)
        json = response.json()
        self.assertEqual(json["username"], u'pmManager')
        # extra_include=categories will return categories of every active configs
        self.assertEqual(len(json["extra_include_categories"]), 2)
        cfg_cat_ids = [cat["id"] for cat in json["extra_include_categories"][cfg_id]]
        cfg2_cat_ids = [cat["id"] for cat in json["extra_include_categories"][cfg2_id]]
        # categories are not enabled in cfg1
        self.assertFalse(cfg_cat_ids)
        self.assertTrue("deployment" in cfg2_cat_ids)
        # can get categories of only one MeetingConfig
        endpoint_url += "&extra_include_categories_configs={0}".format(cfg_id)
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200, response.content)
        json = response.json()
        self.assertEqual(json["username"], u'pmManager')
        self.assertEqual(len(json["extra_include_categories"]), 1)

    def test_restapi_users_classifiers(self):
        """@users?extra_include=classifiers"""
        cfg = self.meetingConfig
        cfg_id = cfg.getId()
        cfg2 = self.meetingConfig2
        cfg2_id = cfg2.getId()
        self._enableField('classifier', cfg2)
        transaction.commit()
        endpoint_url = "{0}/@users/pmManager?extra_include=classifiers".format(
            self.portal_url)
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200, response.content)
        json = response.json()
        self.assertEqual(json["username"], u'pmManager')
        # extra_include=classifiers will return classifiers of every active configs
        self.assertEqual(len(json["extra_include_classifiers"]), 2)
        cfg_cat_ids = [cat["id"] for cat in json["extra_include_classifiers"][cfg_id]]
        cfg2_cat_ids = [cat["id"] for cat in json["extra_include_classifiers"][cfg2_id]]
        # classifiers are not enabled in cfg1
        self.assertFalse(cfg_cat_ids)
        self.assertTrue("classifier1" in cfg2_cat_ids)
        # can get classifiers of only one MeetingConfig
        endpoint_url += "&extra_include_classifiers_configs={0}".format(cfg_id)
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200, response.content)
        json = response.json()
        self.assertEqual(json["username"], u'pmManager')
        self.assertEqual(len(json["extra_include_classifiers"]), 1)


def test_suite():
    from unittest import TestSuite, makeSuite

    suite = TestSuite()
    # add a prefix to avoid every PM tests to be executed
    suite.addTest(makeSuite(testServicePMUsersGet, prefix="test_restapi_"))
    return suite
