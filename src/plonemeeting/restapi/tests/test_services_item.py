# -*- coding: utf-8 -*-

from plonemeeting.restapi.tests.base import BaseTestCase

import transaction


class testServicesItem(BaseTestCase):
    """ """

    def test_restapi_search_items_required_params(self):
        """@search_items"""
        endpoint_url = "{0}/@search_items".format(self.portal_url)
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json(),
                         {u'message': u'The "getConfigId" parameter must be given',
                          u'type': u'Exception'})
        endpoint_url += '?getConfigId={0}'.format(self.meetingConfig.getId())
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200)

    def test_restapi_search_items_endpoint(self):
        """@search_items"""
        endpoint_url = "{0}/@search_items?getConfigId={1}".format(
            self.portal_url, self.meetingConfig.getId())
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200)
        # nothing found for now
        self.assertEqual(response.json()[u'items_total'], 0)

        # create 2 items
        self.changeUser('pmManager')
        item1 = self.create('MeetingItem')
        self.assertEqual(item1.queryState(), 'itemcreated')
        item2 = self.create('MeetingItem')
        self.validateItem(item2)
        self.assertEqual(item2.queryState(), 'validated')
        transaction.commit()

        # found
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.json()[u'items_total'], 2)
        # may still use additional search parameters
        endpoint_url += '&review_state=validated'
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.json()[u'items_total'], 1)
        self.assertEqual(response.json()[u'items'][0][u'review_state'], u'validated')


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    # add a prefix to avoid every PM tests to be executed
    suite.addTest(makeSuite(testServicesItem, prefix='test_restapi_'))
    return suite
