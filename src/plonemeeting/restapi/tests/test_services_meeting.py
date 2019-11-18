# -*- coding: utf-8 -*-

from DateTime import DateTime
from plonemeeting.restapi.tests.base import BaseTestCase

import transaction


class testServicesMeeting(BaseTestCase):
    """ """

    def test_restapi_get_meetings_required_params(self):
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

    def test_restapi_get_meetings_endpoint(self):
        """@search_meetings"""
        endpoint_url = "{0}/@search_meetings?getConfigId={1}".format(
            self.portal_url, self.meetingConfig.getId())
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200)
        # nothing found for now
        self.assertEqual(response.json()[u'items_total'], 0)

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
        self.assertEqual(response.json()[u'items_total'], 1)
        self.assertEqual(response.json()[u'items'][0][u'review_state'], u'closed')

    def test_restapi_get_meeting_items_required_params(self):
        """@search_meeting_items"""
        # getConfigId is required
        base_endpoint_url = "{0}/@search_meeting_items".format(self.portal_url)
        response = self.api_session.get(base_endpoint_url)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.json(),
            {u'message':
                u'The "getConfigId" parameter must be given',
             u'type':
                u'Exception'})
        # getConfigId must be a valid MeetingConfig id
        endpoint_url = base_endpoint_url + '?getConfigId=unknown_id'
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.json(),
            {u'message':
                u'The given "getConfigId" named "unknown_id" was not found',
             u'type':
                u'Exception'})
        # linkedMeetingUID is also a required parameter
        endpoint_url = base_endpoint_url + '?getConfigId={0}'.format(
            self.meetingConfig.getId())
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.json(),
            {u'message': u'The "linkedMeetingUID" parameter must be given',
             u'type': u'Exception'})
        # every parameters provided
        endpoint_url = base_endpoint_url + \
            '?getConfigId={0}&linkedMeetingUID='.format(
                self.meetingConfig.getId())
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[u'items_total'], 0)

    def test_restapi_get_meeting_items_endpoint(self):
        """@search_meeting_items"""
        self.changeUser('pmManager')
        meeting = self._createMeetingWithItems()
        endpoint_url = '{0}/@search_meeting_items?getConfigId={1}&linkedMeetingUID={2}'.format(
            self.portal_url, self.meetingConfig.getId(), meeting.UID())
        transaction.commit()
        response = self.api_session.get(endpoint_url)
        # items are returned sorted
        self.assertEqual(
            [elt['UID'] for elt in response.json()[u'items']],
            [obj.UID() for obj in meeting.getItems(ordered=True)])


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    # add a prefix to avoid every PM tests to be executed
    suite.addTest(makeSuite(testServicesMeeting, prefix='test_restapi_'))
    return suite
