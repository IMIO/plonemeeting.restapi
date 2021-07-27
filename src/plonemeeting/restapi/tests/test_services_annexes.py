# -*- coding: utf-8 -*-

from plonemeeting.restapi.tests.base import BaseTestCase
from Products.PloneMeeting.tests.PloneMeetingTestCase import DEFAULT_USER_PASSWORD
from Products.PloneMeeting.utils import get_annexes

import transaction


class testServiceAnnexes(BaseTestCase):
    """ """

    def tearDown(self):
        self.api_session.close()

    def test_restapi_annexes_endpoint(self):
        """@annexes"""
        endpoint_url = "{0}/@annexes".format(self.portal_url)
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200, response.content)
        # nothing found for now
        self.assertEqual(response.json(), [])

        # create item with annexes
        self.changeUser("pmManager")
        item = self.create("MeetingItem")
        transaction.commit()

        # on MeetingItem without annexes
        item_url = item.absolute_url()
        endpoint_url = "{0}/@annexes".format(item_url)
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.json(), [])
        # add annexes
        self.addAnnex(item)
        self.addAnnex(item)
        response = self.api_session.get(endpoint_url)
        self.assertEqual(len(response.json()), 2)

    def test_restapi_annex_type_only_for_meeting_managers(self):
        """Make sure when a content_category is restricted to MeetingManagers,
           the same information is available in @annexes endpoint."""
        # make 'overhead-analysis' only_for_meeting_managers
        cfg = self.meetingConfig
        financial_analysis = cfg.annexes_types.item_annexes.get("financial-analysis")
        financial_analysis.only_for_meeting_managers = True
        # create item with annexes
        self.changeUser("pmManager")
        item = self.create("MeetingItem")
        item_url = item.absolute_url()
        endpoint_url = "{0}/@annexes?fullobjects".format(item_url)
        annex = self.addAnnex(item)
        transaction.commit()
        self.assertEqual(
            annex.content_category,
            "plonemeeting-assembly-annexes_types_-_item_annexes_-_financial-analysis",
        )
        response_pmManager = self.api_session.get(endpoint_url).json()[0]
        self.changeUser("pmCreator1")
        self.api_session.auth = ("pmCreator1", DEFAULT_USER_PASSWORD)
        response_pmCreator1 = self.api_session.get(endpoint_url).json()[0]
        self.assertEqual(
            response_pmManager["content_category"],
            response_pmCreator1["content_category"],
        )

    def test_restapi_annexes_endpoint_filters(self):
        """@annexes, it is possible to filter on existing boolean values
           to_print, publishable, ..."""
        cfg = self.meetingConfig
        config = cfg.annexes_types.item_annexes
        config.publishable_activated = True
        # create item with annexes
        self.changeUser("pmManager")
        item = self.create("MeetingItem")
        annex = self.addAnnex(item, publishable=True)
        self.addAnnex(item, publishable=False)
        transaction.commit()
        item_url = item.absolute_url()
        endpoint_url = "{0}/@annexes?publishable=true".format(item_url)
        response = self.api_session.get(endpoint_url)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(len(get_annexes(item)), 2)
        annex_infos = response.json()[0]
        self.assertEqual(annex_infos['UID'], annex.UID())

    def test_restapi_annexes_additional_values(self):
        """@annexes, additional_values will actually
        return categorized element infos."""
        self.changeUser("pmManager")
        item = self.create("MeetingItem")
        self.addAnnex(item)
        transaction.commit()
        item_url = item.absolute_url()
        # category_id
        endpoint_url = "{0}/@annexes?fullobjects&include_all=false&" \
            "additional_values=category_id".format(item_url)
        response = self.api_session.get(endpoint_url)
        resp_json = response.json()
        self.assertFalse("category_title" in resp_json[0])
        self.assertEqual(resp_json[0]["category_id"], u'financial-analysis')
        # *
        endpoint_url = "{0}/@annexes?fullobjects&include_all=false&additional_values=*".format(
            item_url)
        response = self.api_session.get(endpoint_url)
        resp_json = response.json()
        self.assertTrue("category_id" in resp_json[0])
        self.assertTrue("category_title" in resp_json[0])
        self.assertTrue("category_uid" in resp_json[0])
        # there are some ignored values
        self.assertFalse("allowedRolesAndUsers" in resp_json[0])
        self.assertFalse("visible_for_groups" in resp_json[0])


def test_suite():
    from unittest import TestSuite, makeSuite

    suite = TestSuite()
    # add a prefix to avoid every PM tests to be executed
    suite.addTest(makeSuite(testServiceAnnexes, prefix="test_restapi_"))
    return suite
