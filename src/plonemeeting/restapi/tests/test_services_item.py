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
        endpoint_url = "{0}/@search_items?getConfigId={1}&fullobjects=True".format(
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
        resp_json = response.json()
        self.assertEqual(resp_json[u'items_total'], 1)
        self.assertEqual(resp_json[u'items'][0][u'review_state'], u'validated')

        # includes every data as well as extra formatted values
        self.assertTrue('motivation' in resp_json['items'][0])
        self.assertTrue('decision' in resp_json['items'][0])
        self.assertTrue('toDiscuss' in resp_json['items'][0])
        self.assertTrue('formatted_itemAssembly' in resp_json['items'][0])
        self.assertTrue('formatted_itemNumber' in resp_json['items'][0])

    def test_restapi_search_items_in_meeting(self):
        """@search_items using the linkedMeetingUID attribute"""
        self.changeUser('pmManager')
        meeting = self._createMeetingWithItems()
        endpoint_url = '{0}/@search_items?getConfigId={1}&linkedMeetingUID={2}' \
            '&sort_on=getItemNumber'.format(
                self.portal_url,
                self.meetingConfig.getId(),
                meeting.UID())
        transaction.commit()
        response = self.api_session.get(endpoint_url)
        # items are returned sorted
        self.assertEqual(
            [elt['UID'] for elt in response.json()[u'items']],
            [obj.UID() for obj in meeting.getItems(ordered=True)])

    def test_restapi_search_items_extra_include(self):
        """@search_items may receive an extra_include parameter"""
        self.changeUser('pmManager')
        self.meetingConfig.setUseGroupsAsCategories(False)
        meeting = self._createMeetingWithItems()
        item = meeting.getItems(ordered=True)[0]
        item.setMotivation('<p>Motivation</p>')
        item.setDecision(self.decisionText)
        endpoint_url = '{0}/@search_items?getConfigId={1}&linkedMeetingUID={2}' \
            '&sort_on=getItemNumber'.format(
                self.portal_url,
                self.meetingConfig.getId(),
                meeting.UID())
        transaction.commit()
        response = self.api_session.get(endpoint_url)
        # by default no extra include
        self.assertFalse('proposingGroup_extra' in response.json()['items'][0])
        # does not work if fullobjects is not used
        endpoint_url = endpoint_url + '&extra_include=proposingGroup'
        response = self.api_session.get(endpoint_url)
        self.assertFalse('proposingGroup_extra' in response.json()['items'][0])
        # now with fullobjects
        endpoint_url = endpoint_url + '&fullobjects'
        response = self.api_session.get(endpoint_url)
        json = response.json()
        self.assertTrue('proposingGroup_extra' in json['items'][0])
        self.assertFalse('category_extra' in json['items'][0])
        # extra_include proposingGroup and category
        endpoint_url = endpoint_url + '&extra_include=category'
        response = self.api_session.get(endpoint_url)
        json = response.json()
        self.assertEqual(json['items'][0]['proposingGroup_extra']['id'], u'developers')
        self.assertEqual(json['items'][0]['category_extra']['id'], u'development')
        # extra_include deliberation
        endpoint_url = endpoint_url + '&extra_include=deliberation'
        response = self.api_session.get(endpoint_url)
        self.assertEqual(
            response.json()['items'][0]['deliberation_extra'],
            {u'public_deliberation': u'<p>Motivation</p><p>Some decision.</p>',
             u'deliberation': u'<p>Motivation</p><p>Some decision.</p>'})


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    # add a prefix to avoid every PM tests to be executed
    suite.addTest(makeSuite(testServicesItem, prefix='test_restapi_'))
    return suite
