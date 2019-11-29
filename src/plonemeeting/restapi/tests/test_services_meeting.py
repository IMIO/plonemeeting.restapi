# -*- coding: utf-8 -*-

from DateTime import DateTime
from plonemeeting.restapi.tests.base import BaseTestCase

import transaction


class testServicesMeeting(BaseTestCase):
    """ """

    def test_restapi_search_meetings_required_params(self):
        """@search_meetings"""
        endpoint_url = "{0}/@search_meetings".format(self.portal_url)
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json(),
                         {u'message': u'The "getConfigId" parameter must be given',
                          u'type': u'Exception'})
        endpoint_url += '?getConfigId={0}'.format(self.meetingConfig.getId())
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200)

    def test_restapi_search_meetings_endpoint(self):
        """@search_meetings"""
        endpoint_url = "{0}/@search_meetings?getConfigId={1}".format(
            self.portal_url, self.meetingConfig.getId())
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200)
        # nothing found for now
        self.assertEqual(response.json()[u'items_total'], 0)

        # create 2 meetings
        self.changeUser('pmManager')
        meeting = self.create('Meeting', date=DateTime('2018/11/18'))
        self.assertEqual(meeting.queryState(), 'created')
        meeting2 = self.create('Meeting', date=DateTime('2019/11/18'))
        self.closeMeeting(meeting2)
        self.assertEqual(meeting2.queryState(), 'closed')
        transaction.commit()

        # found
        response = self.api_session.get(endpoint_url)
        resp_json = response.json()
        self.assertEqual(resp_json[u'items_total'], 2)
        # meetings are sorted by date, from newest to oldest
        self.assertEqual(
            [m['title'] for m in resp_json[u'items']],
            [u'18 november 2019', u'18 november 2018'])
        # may still use additional search parameters
        endpoint_url += '&review_state=closed'
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.json()[u'items_total'], 1)
        self.assertEqual(response.json()[u'items'][0][u'review_state'], u'closed')

    def test_restapi_search_meetings_fullobjects(self):
        """@search_meetings"""
        endpoint_url = "{0}/@search_meetings?getConfigId={1}&fullobjects=True".format(
            self.portal_url, self.meetingConfig.getId())

        # create 2 meetings
        self.changeUser('pmManager')
        meeting = self.create('Meeting', date=DateTime('2019/11/18'))
        self.assertEqual(meeting.queryState(), 'created')
        meeting2 = self.create('Meeting', date=DateTime('2019/11/18'))
        self.closeMeeting(meeting2)
        self.assertEqual(meeting2.queryState(), 'closed')
        transaction.commit()

        # found
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.json()[u'items_total'], 2)
        # may still use additional search parameters
        endpoint_url += '&review_state=closed'
        response = self.api_session.get(endpoint_url)
        resp_json = response.json()
        self.assertEqual(resp_json[u'items_total'], 1)
        self.assertEqual(resp_json[u'items'][0][u'review_state'], u'closed')

        # includes every data as well as extra formatted values
        self.assertTrue('date' in resp_json['items'][0])
        self.assertTrue('startDate' in resp_json['items'][0])
        self.assertTrue('notes' in resp_json['items'][0])
        self.assertTrue('formatted_assembly' in resp_json['items'][0])


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    # add a prefix to avoid every PM tests to be executed
    suite.addTest(makeSuite(testServicesMeeting, prefix='test_restapi_'))
    return suite
