# -*- coding: utf-8 -*-

from plonemeeting.restapi.tests.base import BaseTestCase
from Products.PloneMeeting.tests.PloneMeetingTestCase import DEFAULT_USER_PASSWORD

import transaction


class testServiceAnnexes(BaseTestCase):
    """ """

    def tearDown(self):
        self.api_session.close()

    def test_restapi_annexes_endpoint(self):
        """@annexes"""
        endpoint_url = "{0}/@annexes".format(self.portal_url)
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200)
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
        # contains extra attributes managed by collective.iconifiedcategory
        # as attributes and not in the schema
        annex1_infos = response.json()[0]
        self.assertTrue("category_uid" in annex1_infos)
        self.assertTrue("preview_status" in annex1_infos)
        self.assertTrue("signed_activated" in annex1_infos)
        self.assertTrue("signed" in annex1_infos)
        self.assertTrue("publishable_activated" in annex1_infos)
        self.assertTrue("publishable" in annex1_infos)
        self.assertTrue("to_print" in annex1_infos)

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
        endpoint_url = "{0}/@annexes".format(item_url)
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


def test_suite():
    from unittest import TestSuite, makeSuite

    suite = TestSuite()
    # add a prefix to avoid every PM tests to be executed
    suite.addTest(makeSuite(testServiceAnnexes, prefix="test_restapi_"))
    return suite
