# -*- coding: utf-8 -*-

from plonemeeting.restapi.tests.base import BaseTestCase

import transaction


class testServicesAnnex(BaseTestCase):
    """ """

    def test_restapi_annexes_endpoint(self):
        """@search_items"""
        endpoint_url = "{0}/@annexes".format(self.portal_url)
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200)
        # nothing found for now
        self.assertEqual(response.json(), [])

        # create item with annexes
        self.changeUser('pmManager')
        item = self.create('MeetingItem')
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
        self.assertTrue('category_uid' in annex1_infos)
        self.assertTrue('preview_status' in annex1_infos)
        self.assertTrue('signed_activated' in annex1_infos)
        self.assertTrue('signed' in annex1_infos)
        self.assertTrue('publishable_activated' in annex1_infos)
        self.assertTrue('publishable' in annex1_infos)
        self.assertTrue('to_print' in annex1_infos)


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    # add a prefix to avoid every PM tests to be executed
    suite.addTest(makeSuite(testServicesAnnex, prefix='test_restapi_'))
    return suite
