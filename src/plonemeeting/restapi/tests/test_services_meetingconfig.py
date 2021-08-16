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
        endpoint_url = "{0}/@config".format(self.portal_url)
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.json(), {u"message": CONFIG_ID_ERROR, u"type": u"Exception"}
        )
        endpoint_url += "?config_id={0}".format(self.meetingConfig.getId())
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200, response.content)

    def test_restapi_config_config_id_not_found(self):
        """ """
        endpoint_url = "{0}/@config?config_id=unknown".format(self.portal_url)
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.json(),
            {u"message": CONFIG_ID_NOT_FOUND_ERROR % "unknown", u"type": u"Exception"},
        )

    def test_restapi_config_endpoint(self):
        """@config"""
        cfg = self.meetingConfig
        cfg_id = cfg.getId()
        endpoint_url = "{0}/@config?config_id={1}".format(self.portal_url, cfg_id)
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200, response.content)
        json = response.json()
        # by default, no "items"
        self.assertFalse("items" in json)
        self.assertEqual(json["id"], cfg_id)
        self.assertEqual(json["UID"], cfg.UID())

    def test_restapi_config_extra_include_categories(self):
        """@config"""
        # cfg2 uses disabled categories
        cfg = self.meetingConfig2
        cfg.setUseGroupsAsCategories(False)
        cfg_id = cfg.getId()
        transaction.commit()
        # categories
        endpoint_url_pattern = "{0}/@config?config_id={1}&extra_include={2}"
        endpoint_url = endpoint_url_pattern.format(self.portal_url, cfg_id, "categories")
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200, response.content)
        json = response.json()
        categories = json["extra_include_categories"]
        self.assertEqual(categories[0]["id"], u"deployment")
        self.assertEqual(categories[0]["@type"], u"meetingcategory")
        self.assertEqual(categories[0]["enabled"], True)
        self.assertEqual(categories[0]["review_state"], None)
        # disabled categories are also returned
        self.assertEqual(categories[-2]["id"], u"marketing")
        self.assertEqual(categories[-2]["@type"], u"meetingcategory")
        self.assertEqual(categories[-2]["enabled"], False)
        self.assertEqual(categories[-2]["review_state"], None)

    def test_restapi_config_extra_include_classifiers(self):
        """@config"""
        cfg = self.meetingConfig
        cfg_id = cfg.getId()
        endpoint_url_pattern = "{0}/@config?config_id={1}&extra_include={2}"
        endpoint_url = endpoint_url_pattern.format(self.portal_url, cfg_id, "classifiers")
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200, response.content)
        json = response.json()
        classifiers = json["extra_include_classifiers"]
        self.assertEqual(len(classifiers), 3)
        self.assertEqual(classifiers[0]["id"], u"classifier1")
        self.assertEqual(classifiers[0]["@type"], u"meetingcategory")
        self.assertEqual(classifiers[0]["enabled"], True)
        self.assertEqual(classifiers[0]["review_state"], None)
        self.assertEqual(classifiers[1]["id"], u"classifier2")
        self.assertEqual(classifiers[2]["id"], u"classifier3")

    def test_restapi_config_extra_include_pod_templates(self):
        """@config"""
        cfg = self.meetingConfig
        cfg_id = cfg.getId()
        endpoint_url_pattern = "{0}/@config?config_id={1}&extra_include={2}"
        endpoint_url = endpoint_url_pattern.format(
            self.portal_url, cfg_id, "pod_templates"
        )
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200, response.content)
        json = response.json()
        pod_templates = json["extra_include_pod_templates"]
        self.assertEqual(pod_templates[0]["id"], u"styles1")
        self.assertEqual(pod_templates[0]["@type"], u"StyleTemplate")
        self.assertEqual(pod_templates[4]["id"], u"itemTemplate")
        self.assertEqual(pod_templates[4]["@type"], u"ConfigurablePODTemplate")
        itemTemplate = cfg.podtemplates.itemTemplate
        self.assertEqual(len(pod_templates), 7)
        self.assertTrue(itemTemplate.Title() in [template['title'] for template in pod_templates])
        # only enabled POD templates are returned
        transaction.begin()
        itemTemplate.enabled = False
        itemTemplate.reindexObject()
        transaction.commit()
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200, response.content)
        json = response.json()
        pod_templates = json["extra_include_pod_templates"]
        self.assertEqual(len(pod_templates), 6)
        self.assertFalse(itemTemplate.Title() in [template['title'] for template in pod_templates])

    def test_restapi_config_extra_include_searches(self):
        """@config extra_include=searches"""
        cfg = self.meetingConfig
        cfg_id = cfg.getId()
        endpoint_url_pattern = "{0}/@config?config_id={1}&extra_include={2}"
        endpoint_url = endpoint_url_pattern.format(self.portal_url, cfg_id, "searches")
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200, response.content)
        json = response.json()
        searches = json["extra_include_searches"]
        self.assertEqual(searches[0]["id"], u"searchmyitems")
        self.assertEqual(searches[0]["@type"], u"DashboardCollection")
        # include_items is set to False specifically
        self.assertFalse("items" in searches[0])
        searchmyitems = cfg.searches.searches_items.searchmyitems
        self.assertTrue(searchmyitems.Title() in [search['title'] for search in searches])

        # only enabled DashboardCollections are returned
        transaction.begin()
        searchmyitems.enabled = False
        searchmyitems.reindexObject()
        transaction.commit()
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200, response.content)
        json = response.json()
        searches = json["extra_include_searches"]
        self.assertNotEqual(searches[0]["id"], u"searchmyitems")
        self.assertEqual(searches[0]["@type"], u"DashboardCollection")
        self.assertFalse(searchmyitems.Title() in [search['title'] for search in searches])

    def test_restapi_config_extra_include_proposing_groups(self):
        """@config extra_include=proposing_groups"""
        cfg = self.meetingConfig
        cfg_id = cfg.getId()
        endpoint_url_pattern = "{0}/@config?config_id={1}&extra_include={2}"
        endpoint_url = endpoint_url_pattern.format(self.portal_url, cfg_id, "proposing_groups")
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200, response.content)
        json = response.json()
        orgs = json["extra_include_proposing_groups"]
        self.assertEqual(orgs[0]['UID'], self.developers_uid)
        self.assertEqual(orgs[1]['UID'], self.vendors_uid)

    def test_restapi_config_extra_include_associated_groups(self):
        """@config extra_include=associated_groups"""
        cfg = self.meetingConfig
        cfg_id = cfg.getId()
        endpoint_url_pattern = "{0}/@config?config_id={1}&extra_include={2}"
        endpoint_url = endpoint_url_pattern.format(self.portal_url, cfg_id, "associated_groups")
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200, response.content)
        json = response.json()
        orgs = json["extra_include_associated_groups"]
        self.assertEqual(orgs[0]['UID'], self.developers_uid)
        self.assertEqual(orgs[1]['UID'], self.vendors_uid)

    def test_restapi_config_extra_include_groups_in_charge(self):
        """@config extra_include=groups_in_charge"""
        cfg = self.meetingConfig
        cfg_id = cfg.getId()
        self._enableField('groupsInCharge')
        transaction.commit()
        endpoint_url_pattern = "{0}/@config?config_id={1}&extra_include={2}"
        endpoint_url = endpoint_url_pattern.format(self.portal_url, cfg_id, "groups_in_charge")
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200, response.content)
        json = response.json()
        orgs = json["extra_include_groups_in_charge"]
        self.assertEqual(orgs[0]['UID'], self.developers_uid)
        self.assertEqual(orgs[1]['UID'], self.vendors_uid)

    def test_restapi_config_extra_include_fullobjects(self):
        """@config extra_include_fullobjects"""
        cfg = self.meetingConfig
        cfg_id = cfg.getId()
        self._enableField('groupsInCharge')
        cfg.setUseGroupsAsCategories(False)
        cfg_id = cfg.getId()
        transaction.commit()
        endpoint_url_pattern = "{0}/@config?config_id={1}&extra_include={2}" \
            "&extra_include={3}&extra_include={4}&extra_include={5}" \
            "&extra_include={6}&extra_include={7}"
        endpoint_url = endpoint_url_pattern.format(
            self.portal_url,
            cfg_id,
            "categories",
            "pod_templates",
            "searches",
            "associated_groups",
            "groups_in_charge",
            "proposing_groups")
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200, response.content)
        json = response.json()
        # by default, we only get summarized versions
        self.assertFalse("@components" in json['extra_include_categories'][0])
        self.assertFalse("@components" in json['extra_include_pod_templates'][0])
        self.assertFalse("@components" in json['extra_include_searches'][0])
        self.assertFalse("@components" in json['extra_include_associated_groups'][0])
        self.assertFalse("@components" in json['extra_include_groups_in_charge'][0])
        self.assertFalse("@components" in json['extra_include_proposing_groups'][0])
        # parameter "extra_include_xxx_fullobjects" will get full serialized versions
        endpoint_url += "&extra_include_categories_fullobjects"
        endpoint_url += "&extra_include_pod_templates_fullobjects"
        endpoint_url += "&extra_include_searches_fullobjects"
        endpoint_url += "&extra_include_associated_groups_fullobjects"
        endpoint_url += "&extra_include_groups_in_charge_fullobjects"
        endpoint_url += "&extra_include_proposing_groups_fullobjects"
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200, response.content)
        json = response.json()
        self.assertTrue("@components" in json['extra_include_categories'][0])
        self.assertTrue("@components" in json['extra_include_pod_templates'][0])
        self.assertTrue("@components" in json['extra_include_searches'][0])
        self.assertTrue("@components" in json['extra_include_associated_groups'][0])
        self.assertTrue("@components" in json['extra_include_groups_in_charge'][0])
        self.assertTrue("@components" in json['extra_include_proposing_groups'][0])


def test_suite():
    from unittest import TestSuite, makeSuite

    suite = TestSuite()
    # add a prefix to avoid every PM tests to be executed
    suite.addTest(makeSuite(testServiceConfig, prefix="test_restapi_"))
    return suite
