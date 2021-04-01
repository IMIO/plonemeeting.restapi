# -*- coding: utf-8 -*-

from DateTime import DateTime
from plonemeeting.restapi.config import CONFIG_ID_ERROR
from plonemeeting.restapi.config import CONFIG_ID_NOT_FOUND_ERROR
from plonemeeting.restapi.config import IN_NAME_OF_UNAUTHORIZED
from plonemeeting.restapi.tests.base import BaseTestCase
from plonemeeting.restapi.utils import IN_NAME_OF_USER_NOT_FOUND
from Products.PloneMeeting.tests.PloneMeetingTestCase import DEFAULT_USER_PASSWORD

import transaction


class testServiceSearch(BaseTestCase):
    """@search without 'type' is the same as @search?type=item"""

    def tearDown(self):
        self.api_session.close()

    def test_restapi_search_items_required_params(self):
        """ """
        endpoint_url = "{0}/@search".format(self.portal_url)
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.json(), {u"message": CONFIG_ID_ERROR, u"type": u"Exception"}
        )
        endpoint_url += "?config_id={0}".format(self.meetingConfig.getId())
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200)

    def test_restapi_search_config_id_not_found(self):
        """ """
        endpoint_url = "{0}/@search?config_id=unknown".format(self.portal_url)
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.json(),
            {u"message": CONFIG_ID_NOT_FOUND_ERROR % "unknown", u"type": u"Exception"},
        )

    def test_restapi_search_items_endpoint(self):
        """ """
        endpoint_url = "{0}/@search?config_id={1}&fullobjects=True".format(
            self.portal_url, self.meetingConfig.getId()
        )
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200)
        # nothing found for now
        self.assertEqual(response.json()[u"items_total"], 0)

        # create 2 items
        self.changeUser("pmManager")
        item1 = self.create("MeetingItem")
        self.assertEqual(item1.queryState(), "itemcreated")
        item2 = self.create("MeetingItem")
        self.validateItem(item2)
        self.assertEqual(item2.queryState(), "validated")
        transaction.commit()

        # found
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.json()[u"items_total"], 2)
        # may still use additional search parameters
        endpoint_url += "&review_state=validated"
        response = self.api_session.get(endpoint_url)
        resp_json = response.json()
        self.assertEqual(resp_json[u"items_total"], 1)
        self.assertEqual(resp_json[u"items"][0][u"review_state"], u"validated")

        # includes every data as well as extra formatted values
        self.assertTrue("motivation" in resp_json["items"][0])
        self.assertTrue("decision" in resp_json["items"][0])
        self.assertTrue("toDiscuss" in resp_json["items"][0])
        self.assertTrue("formatted_itemAssembly" in resp_json["items"][0])
        self.assertTrue("formatted_itemNumber" in resp_json["items"][0])
        self.assertTrue("all_copyGroups" in resp_json["items"][0])
        self.assertTrue("all_groupsInCharge" in resp_json["items"][0])
        transaction.abort()

    def test_restapi_search_items_in_meeting(self):
        """@search using the linkedMeetingUID attribute"""
        self.changeUser("pmManager")
        meeting = self._createMeetingWithItems()
        endpoint_url = (
            "{0}/@search?config_id={1}&linkedMeetingUID={2}"
            "&sort_on=getItemNumber".format(
                self.portal_url, self.meetingConfig.getId(), meeting.UID()
            )
        )
        transaction.commit()
        response = self.api_session.get(endpoint_url)
        # items are returned sorted
        self.assertEqual(
            [elt["UID"] for elt in response.json()[u"items"]],
            [obj.UID() for obj in meeting.getItems(ordered=True)],
        )
        transaction.abort()

    def test_restapi_search_items_extra_include(self):
        """@search may receive an extra_include parameter"""
        transaction.begin()
        cfg = self.meetingConfig
        self.changeUser("pmManager")
        cfg.setUseGroupsAsCategories(False)
        self.getMeetingFolder()
        meeting = self.create("Meeting", date=DateTime("2020/06/08 08:00"))
        item = self.create("MeetingItem")
        item.setMotivation("<p>Motivation</p>")
        item.setDecision(self.decisionText)
        self.presentItem(item)
        endpoint_url = (
            "{0}/@search?config_id={1}&linkedMeetingUID={2}"
            "&sort_on=getItemNumber".format(
                self.portal_url, self.meetingConfig.getId(), meeting.UID()
            )
        )
        transaction.commit()
        response = self.api_session.get(endpoint_url)
        # by default no extra include
        self.assertFalse("extra_include_proposingGroup" in response.json()["items"][0])
        # does not work if fullobjects is not used
        endpoint_url = endpoint_url + "&extra_include=proposingGroup"
        response = self.api_session.get(endpoint_url)
        self.assertFalse("extra_include_proposingGroup" in response.json()["items"][0])
        # now with fullobjects
        endpoint_url = endpoint_url + "&fullobjects"
        response = self.api_session.get(endpoint_url)
        json = response.json()
        self.assertTrue("extra_include_proposingGroup" in json["items"][0])
        self.assertFalse("extra_include_category" in json["items"][0])
        # extra_include proposingGroup and category
        endpoint_url = endpoint_url + "&extra_include=category"
        transaction.begin()
        response = self.api_session.get(endpoint_url)
        json = response.json()
        self.assertEqual(
            json["items"][0]["extra_include_proposingGroup"]["id"], u"developers"
        )
        self.assertEqual(
            json["items"][0]["extra_include_category"]["id"], u"development"
        )
        # extra_include deliberation
        endpoint_url = endpoint_url + "&extra_include=deliberation"
        response = self.api_session.get(endpoint_url)
        self.assertEqual(
            response.json()["items"][0]["extra_include_deliberation"],
            {
                u"deliberation": u"<p>Motivation</p><p>Some decision.</p>",
            },
        )
        # extra_include several deliberation variants
        endpoint_url = endpoint_url + "&extra_include=deliberation"
        endpoint_url = endpoint_url + "&extra_include=public_deliberation"
        endpoint_url = endpoint_url + "&extra_include=public_deliberation_decided"
        response = self.api_session.get(endpoint_url)
        self.assertEqual(
            response.json()["items"][0]["extra_include_deliberation"],
            {
                u"deliberation": u"<p>Motivation</p><p>Some decision.</p>",
                u"public_deliberation": u"<p>Motivation</p><p>Some decision.</p>",
                u"public_deliberation_decided": u"<p>Motivation</p><p>Some decision.</p>",
            },
        )
        # extra_include meeting
        endpoint_url = endpoint_url + "&extra_include=meeting"
        response = self.api_session.get(endpoint_url)
        self.assertEqual(
            response.json()["items"][0]["extra_include_meeting"]["UID"],
            meeting.UID()
        )
        self.assertEqual(
            response.json()["items"][0]["extra_include_meeting"]["formatted_date"],
            u'08/06/2020 (08:00)'
        )
        self.assertEqual(
            response.json()["items"][0]["extra_include_meeting"]["formatted_date_short"],
            u'08/06/2020'
        )
        self.assertEqual(
            response.json()["items"][0]["extra_include_meeting"]["formatted_date_long"],
            u'08 june 2020 (08:00)'
        )
        transaction.abort()

    def test_restapi_search_meetings_required_params(self):
        """@search?type=meeting"""
        endpoint_url = "{0}/@search?type=meeting".format(self.portal_url)
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.json(), {u"message": CONFIG_ID_ERROR, u"type": u"Exception"}
        )
        endpoint_url += "&config_id={0}".format(self.meetingConfig.getId())
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200)

    def test_restapi_search_meetings_endpoint(self):
        """ """
        endpoint_url = "{0}/@search?config_id={1}&type=meeting".format(
            self.portal_url, self.meetingConfig.getId()
        )
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200)
        # nothing found for now
        self.assertEqual(response.json()[u"items_total"], 0)

        # create 2 meetings
        self.changeUser("pmManager")
        meeting = self.create("Meeting", date=DateTime("2018/11/18"))
        self.assertEqual(meeting.queryState(), "created")
        meeting2 = self.create("Meeting", date=DateTime("2019/11/18"))
        self.closeMeeting(meeting2)
        self.assertEqual(meeting2.queryState(), "closed")
        transaction.commit()

        # found
        response = self.api_session.get(endpoint_url)
        resp_json = response.json()
        self.assertEqual(resp_json[u"items_total"], 2)
        # meetings are sorted by date, from newest to oldest
        self.assertEqual(
            [m["title"] for m in resp_json[u"items"]],
            [u"18 november 2019", u"18 november 2018"],
        )
        # may still use additional search parameters
        endpoint_url += "&review_state=closed"
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.json()[u"items_total"], 1)
        self.assertEqual(response.json()[u"items"][0][u"review_state"], u"closed")
        transaction.abort()

    def test_restapi_search_meetings_fullobjects(self):
        """ """
        endpoint_url = "{0}/@search?config_id={1}&type=meeting&fullobjects=True".format(
            self.portal_url, self.meetingConfig.getId()
        )

        # create 2 meetings
        self.changeUser("pmManager")
        meeting = self.create("Meeting", date=DateTime("2019/11/18"))
        self.assertEqual(meeting.queryState(), "created")
        meeting2 = self.create("Meeting", date=DateTime("2019/11/18"))
        self.closeMeeting(meeting2)
        self.assertEqual(meeting2.queryState(), "closed")
        transaction.commit()

        # found
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.json()[u"items_total"], 2)
        # may still use additional search parameters
        endpoint_url += "&review_state=closed"
        response = self.api_session.get(endpoint_url)
        resp_json = response.json()
        self.assertEqual(resp_json[u"items_total"], 1)
        self.assertEqual(resp_json[u"items"][0][u"review_state"], u"closed")

        # includes every data as well as extra formatted values
        self.assertTrue("date" in resp_json["items"][0])
        self.assertTrue("startDate" in resp_json["items"][0])
        self.assertTrue("notes" in resp_json["items"][0])
        self.assertTrue("formatted_assembly" in resp_json["items"][0])
        transaction.abort()

    def test_restapi_search_meetings_accepting_items(self):
        """ """
        cfg = self.meetingConfig
        endpoint_url = "{0}/@search?config_id={1}&type=meeting".format(
            self.portal_url, cfg.getId()
        )

        # create 2 meetings
        self.changeUser("pmManager")
        meeting = self.create("Meeting", date=DateTime("2020/05/10"))
        self.assertEqual(meeting.queryState(), "created")
        meeting2 = self.create("Meeting", date=DateTime("2020/05/17"))
        self.closeMeeting(meeting2)
        self.assertEqual(meeting2.queryState(), "closed")
        transaction.commit()
        # only meeting is accepting items
        self.assertEqual(
            [meeting.UID()], [brain.UID for brain in cfg.getMeetingsAcceptingItems()]
        )

        # both found by default
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.json()[u"items_total"], 2)
        endpoint_url += "&meetings_accepting_items=True"
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.json()[u"items_total"], 1)

    def test_restapi_search_in_name_of(self):
        """ """
        cfg = self.meetingConfig
        endpoint_url_pattern = "{0}/@search?config_id={1}&in_name_of=%s".format(
            self.portal_url, cfg.getId()
        )
        # must be (Meeting)Manager to use in_name_of
        self.api_session.auth = ("pmCreator1", DEFAULT_USER_PASSWORD)
        response = self.api_session.get(endpoint_url_pattern % "pmCreator2")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.json(),
            {
                u"message": IN_NAME_OF_UNAUTHORIZED % "pmCreator2",
                u"type": u"Unauthorized",
            },
        )
        # user must exist
        self.api_session.auth = ("pmManager", DEFAULT_USER_PASSWORD)
        response = self.api_session.get(endpoint_url_pattern % "unknown")
        self.assertEqual(
            response.json(),
            {u"message": IN_NAME_OF_USER_NOT_FOUND % "unknown", u"type": u"BadRequest"},
        )
        # create 2 items, one for developers, one for vendors
        self.api_session.auth = ("pmManager", DEFAULT_USER_PASSWORD)
        self._addPrincipalToGroup("pmManager", self.vendors_creators)
        self.changeUser("pmManager")
        item1 = self.create("MeetingItem", proposingGroup=self.developers_uid)
        item2 = self.create("MeetingItem", proposingGroup=self.vendors_uid)
        transaction.commit()
        # both found by default
        response = self.api_session.get(endpoint_url_pattern % "")
        self.assertEqual(response.json()[u"items_total"], 2)
        # as pmCreator1, only item1 found
        response = self.api_session.get(endpoint_url_pattern % "pmCreator1")
        self.assertEqual(response.json()[u"items_total"], 1)
        self.assertEqual(response.json()["items"][0][u"UID"], item1.UID())
        # as pmCreator2, only item2 found
        response = self.api_session.get(endpoint_url_pattern % "pmCreator2")
        self.assertEqual(response.json()[u"items_total"], 1)
        self.assertEqual(response.json()["items"][0][u"UID"], item2.UID())

    def test_restapi_search_base_search_uid(self):
        """A collection UID may be given as base search."""
        cfg = self.meetingConfig
        # use the searchdecideditems collection
        base_search_uid = self.meetingConfig.searches.searches_items.searchmyitems.UID()
        endpoint_url = "{0}/@search?config_id={1}&base_search_uid={2}".format(
            self.portal_url, cfg.getId(), base_search_uid
        )
        response = self.api_session.get(endpoint_url)
        # nothing found for now
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[u"items_total"], 0)
        # create one item for developers and one for vendors as pmManager
        # and one item as pmCreator1
        self.changeUser("pmCreator1")
        item_dev1 = self.create("MeetingItem", proposingGroup=self.developers_uid)
        item_dev1_uid = item_dev1.UID()
        self._addPrincipalToGroup("pmManager", self.vendors_creators)
        self.changeUser("pmManager")
        item_dev2 = self.create("MeetingItem", proposingGroup=self.developers_uid)
        item_dev2_uid = item_dev2.UID()
        item_ven1 = self.create("MeetingItem", proposingGroup=self.vendors_uid)
        item_ven1_uid = item_ven1.UID()
        transaction.commit()
        response = self.api_session.get(endpoint_url)
        json = response.json()
        # only 2 items found
        self.assertEqual(json[u"items_total"], 2)
        self.assertEqual(json[u"items"][0]["UID"], item_dev2_uid)
        self.assertEqual(json[u"items"][1]["UID"], item_ven1_uid)
        # possible to complete the query with arbitray parameters
        # restrict only developers_uid
        endpoint_url += "&getProposingGroup={0}".format(self.developers_uid)
        response = self.api_session.get(endpoint_url)
        json = response.json()
        # only 1 item found
        self.assertEqual(json[u"items_total"], 1)
        self.assertEqual(json[u"items"][0]["UID"], item_dev2_uid)
        # override Creator, use pmCreator1
        endpoint_url += "&Creator=pmCreator1"
        response = self.api_session.get(endpoint_url)
        json = response.json()
        self.assertEqual(json[u"items_total"], 1)
        self.assertEqual(json[u"items"][0]["UID"], item_dev1_uid)
        # get items from pmManager and pmCreator1
        endpoint_url += "&Creator=pmManager"
        response = self.api_session.get(endpoint_url)
        json = response.json()
        self.assertEqual(json[u"items_total"], 2)
        self.assertEqual(json[u"items"][0]["UID"], item_dev1_uid)
        self.assertEqual(json[u"items"][1]["UID"], item_dev2_uid)


def test_suite():
    from unittest import TestSuite, makeSuite

    suite = TestSuite()
    # add a prefix to avoid every PM tests to be executed
    suite.addTest(makeSuite(testServiceSearch, prefix="test_restapi_"))
    return suite
