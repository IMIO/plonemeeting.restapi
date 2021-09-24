# -*- coding: utf-8 -*-

from datetime import datetime
from imio.helpers.content import richtextval
from plone.app.textfield.value import RichTextValue
from plonemeeting.restapi.config import CONFIG_ID_ERROR
from plonemeeting.restapi.config import CONFIG_ID_NOT_FOUND_ERROR
from plonemeeting.restapi.config import IN_NAME_OF_UNAUTHORIZED
from plonemeeting.restapi.serializer.meeting import HAS_MEETING_DX
from plonemeeting.restapi.tests.base import BaseTestCase
from plonemeeting.restapi.utils import IN_NAME_OF_USER_NOT_FOUND
from Products.PloneMeeting.MeetingItem import MeetingItem
from Products.PloneMeeting.tests.PloneMeetingTestCase import DEFAULT_USER_PASSWORD
from Products.PloneMeeting.tests.PloneMeetingTestCase import IMG_BASE64_DATA

import transaction


class testServiceSearch(BaseTestCase):
    """@search without 'type' is the same as @search?type=item"""

    def tearDown(self):
        self.api_session.close()

    def test_restapi_search_config_id_not_found(self):
        """Wrong config_id."""
        endpoint_url = "{0}/@search?config_id=unknown".format(self.portal_url)
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.json(),
            {u"message": CONFIG_ID_NOT_FOUND_ERROR % "unknown", u"type": u"Exception"},
        )

    def test_restapi_search_config_id_error(self):
        """Parameter config_id is required when type is "item" or "meeting"."""
        # item
        endpoint_url = "{0}/@search?type=item".format(self.portal_url)
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.json(),
            {u"message": CONFIG_ID_ERROR, u"type": u"Exception"},
        )
        # meeting
        endpoint_url = "{0}/@search?type=meeting".format(self.portal_url)
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.json(),
            {u"message": CONFIG_ID_ERROR, u"type": u"Exception"},
        )
        # works for another type
        endpoint_url = "{0}/@search?type=Folder".format(self.portal_url)
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200, response.content)
        resp_json = response.json()
        self.assertEqual(resp_json[u"items"][0][u"@type"], u"Folder")
        self.assertEqual(resp_json[u"items"][-1][u"@type"], u"Folder")

    def test_restapi_search_items_endpoint(self):
        """ """
        endpoint_url = "{0}/@search?config_id={1}&fullobjects=True".format(
            self.portal_url, self.meetingConfig.getId()
        )
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200, response.content)
        # nothing found for now
        self.assertEqual(response.json()[u"items_total"], 0)

        # create 2 items
        self.changeUser("pmManager")
        item1 = self.create("MeetingItem")
        self.assertEqual(self.get_review_state(item1), "itemcreated")
        item2 = self.create("MeetingItem")
        self.validateItem(item2)
        self.assertEqual(self.get_review_state(item2), "validated")
        transaction.commit()

        # found
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()[u"items_total"], 2)
        # may still use additional search parameters
        endpoint_url += "&review_state=validated"
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200, response.content)
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
        self.assertEqual(response.status_code, 200, response.content)
        # items are returned sorted
        items_getter = HAS_MEETING_DX and meeting.get_items or meeting.getItems
        self.assertEqual(
            [elt["UID"] for elt in response.json()[u"items"]],
            [obj.UID() for obj in items_getter(ordered=True)],
        )
        transaction.abort()

    def test_restapi_search_items_extra_include(self):
        """@search may receive an extra_include parameter"""
        transaction.begin()
        cfg = self.meetingConfig
        self.changeUser("pmManager")
        cfg.setUseGroupsAsCategories(False)
        self._enableField("groupsInCharge")
        self.getMeetingFolder()
        meeting = self.create("Meeting", date=datetime(2020, 6, 8, 8, 0))
        item = self.create("MeetingItem",
                           classifier="classifier1",
                           groupsInCharge=(self.developers_uid, ),
                           associatedGroups=(self.vendors_uid, ))
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
        self.assertEqual(response.status_code, 200, response.content)
        # by default no extra include
        self.assertFalse("extra_include_proposing_group" in response.json()["items"][0])
        # does work even when fullobjects is not used
        endpoint_url = endpoint_url + "&extra_include=proposing_group"
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200, response.content)
        self.assertTrue("extra_include_proposing_group" in response.json()["items"][0])
        # now with fullobjects
        endpoint_url = endpoint_url + "&fullobjects"
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200, response.content)
        json = response.json()
        self.assertTrue("extra_include_proposing_group" in json["items"][0])
        self.assertFalse("extra_include_category" in json["items"][0])
        # extra_include proposing_group and category
        endpoint_url = endpoint_url + "&extra_include=category"
        transaction.begin()
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200, response.content)
        json = response.json()
        self.assertEqual(
            json["items"][0]["extra_include_proposing_group"]["id"], u"developers"
        )
        self.assertEqual(
            json["items"][0]["extra_include_category"]["id"], u"development"
        )
        # extra_include deliberation
        response = self.api_session.get(endpoint_url + "&extra_include=deliberation")
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(
            response.json()["items"][0]["extra_include_deliberation"],
            {
                u"deliberation": u"<p>Motivation</p><p>Some decision.</p>",
            },
        )
        # extra_include several deliberation variants, but not "deliberation"
        endpoint_url = endpoint_url + "&extra_include=public_deliberation"
        endpoint_url = endpoint_url + "&extra_include=public_deliberation_decided"
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(
            response.json()["items"][0]["extra_include_deliberation"],
            {
                u"public_deliberation": u"<p>Motivation</p><p>Some decision.</p>",
                u"public_deliberation_decided": u"<p>Motivation</p><p>Some decision.</p>",
            },
        )
        # extra_include meeting, need to pass also
        # extra_include_meeting_additional_values=*
        # to get additional_values like "formatted_date"
        endpoint_url = endpoint_url + \
            "&extra_include=meeting&extra_include_meeting_additional_values=*"
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200, response.content)
        resp_json = response.json()
        self.assertEqual(
            resp_json["items"][0]["extra_include_meeting"]["UID"],
            meeting.UID()
        )
        self.assertEqual(
            resp_json["items"][0]["extra_include_meeting"]["formatted_date"],
            u'08/06/2020 (08:00)'
        )
        self.assertEqual(
            resp_json["items"][0]["extra_include_meeting"]["formatted_date_short"],
            u'08/06/2020'
        )
        self.assertEqual(
            resp_json["items"][0]["extra_include_meeting"]["formatted_date_long"],
            u'08 june 2020 (08:00)'
        )
        # extra_include everything
        endpoint_url = endpoint_url + "&extra_include=classifier"
        endpoint_url = endpoint_url + "&extra_include=groups_in_charge"
        endpoint_url = endpoint_url + "&extra_include=associated_groups"
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200, response.content)
        resp_json = response.json()
        # by default, extra_include are summary
        self.assertFalse("@components" in resp_json["items"][0]["extra_include_category"])
        self.assertFalse("@components" in resp_json["items"][0]["extra_include_classifier"])
        self.assertFalse("@components" in resp_json["items"][0]["extra_include_meeting"])
        self.assertFalse("@components" in resp_json["items"][0]["extra_include_proposing_group"])
        self.assertFalse("@components" in resp_json["items"][0]["extra_include_groups_in_charge"])
        self.assertFalse("@components" in resp_json["items"][0]["extra_include_associated_groups"])
        # extra_include_fullobjects
        endpoint_url = endpoint_url + "&extra_include_category_fullobjects"
        endpoint_url = endpoint_url + "&extra_include_classifier_fullobjects"
        endpoint_url = endpoint_url + "&extra_include_meeting_fullobjects"
        endpoint_url = endpoint_url + "&extra_include_proposing_group_fullobjects"
        endpoint_url = endpoint_url + "&extra_include_groups_in_charge_fullobjects"
        endpoint_url = endpoint_url + "&extra_include_associated_groups_fullobjects"
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200, response.content)
        resp_json = response.json()
        self.assertTrue("@components" in resp_json["items"][0]["extra_include_category"])
        self.assertTrue("@components" in resp_json["items"][0]["extra_include_classifier"])
        self.assertTrue("@components" in resp_json["items"][0]["extra_include_proposing_group"])
        self.assertTrue("@components" in resp_json["items"][0]["extra_include_groups_in_charge"][0])
        self.assertTrue("@components" in resp_json["items"][0]["extra_include_associated_groups"][0])
        self.assertTrue("@components" in resp_json["items"][0]["extra_include_meeting"])
        self.assertEqual(resp_json["items"][0]["extra_include_classifier"]["id"],
                         "classifier1")
        self.assertEqual(resp_json["items"][0]["extra_include_groups_in_charge"][0]["id"],
                         "developers")
        self.assertEqual(resp_json["items"][0]["extra_include_associated_groups"][0]["id"],
                         "vendors")

        # for meeting moreover by default include_items=False
        # in AT Meeting, we have a field called "items"...
        if HAS_MEETING_DX:
            self.assertFalse("items" in resp_json["items"][0]["extra_include_meeting"])
        endpoint_url = endpoint_url + "&extra_include_meeting_include_items=true"
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200, response.content)
        resp_json = response.json()
        self.assertTrue("@components" in resp_json["items"][0]["extra_include_meeting"])
        self.assertTrue("items" in resp_json["items"][0]["extra_include_meeting"])
        transaction.abort()

    def test_restapi_search_items_extra_include_deliberation_images(self):
        """When asking for "deliberation" values, images are data base64 values"""
        transaction.begin()
        cfg = self.meetingConfig
        self.changeUser("pmManager")
        cfg.setUseGroupsAsCategories(False)
        self.getMeetingFolder()
        item = self.create("MeetingItem")
        item.setMotivation("<p>Motivation</p>")
        img = self._add_image(item)
        pattern = '<p>Text with image <img src="{0}"/> and more text.</p>'
        text = pattern.format(img.absolute_url())
        item.setDecision(text)
        endpoint_url = "{0}/@search?config_id={1}&type=item&fullobjects" \
            "&extra_include=deliberation_decision".format(
                self.portal_url, self.meetingConfig.getId())
        transaction.commit()
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200, response.content)
        resp_json = response.json()
        self.assertEqual(
            resp_json["items"][0]["extra_include_deliberation"]["deliberation_decision"],
            pattern.format(IMG_BASE64_DATA))

    def test_restapi_search_meetings_endpoint(self):
        """ """
        endpoint_url = "{0}/@search?config_id={1}&type=meeting".format(
            self.portal_url, self.meetingConfig.getId()
        )
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200, response.content)
        # nothing found for now
        self.assertEqual(response.json()[u"items_total"], 0)

        # create 2 meetings
        self.changeUser("pmManager")
        meeting = self.create("Meeting", date=datetime(2018, 11, 18))
        self.assertEqual(self.get_review_state(meeting), "created")
        meeting2 = self.create("Meeting", date=datetime(2019, 11, 18))
        self.closeMeeting(meeting2)
        self.assertEqual(self.get_review_state(meeting2), "closed")
        transaction.commit()

        # found
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200, response.content)
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
        self.assertEqual(response.status_code, 200, response.content)
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
        pattern = '<p>Text with image <img src="{0}"/> and more text.</p>'
        meeting = self.create("Meeting", date=datetime(2019, 11, 18))
        meeting2 = self.create("Meeting", date=datetime(2019, 11, 19))
        if HAS_MEETING_DX:
            meeting2.assembly = RichTextValue(u'Mr Present, [[Mr Absent]], Mr Present2')
            img = self._add_image(meeting2)
            text = pattern.format(img.absolute_url())
            meeting2.observations = richtextval(text)
        else:
            meeting2.setAssembly(u'Mr Present, [[Mr Absent]], Mr Present2')
            img = self._add_image(meeting2)
            text = pattern.format(img.absolute_url())
            meeting2.setObservations(text)

        self.assertEqual(self.get_review_state(meeting), "created")
        self.closeMeeting(meeting2)
        self.assertEqual(self.get_review_state(meeting2), "closed")
        transaction.commit()

        # found
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()[u"items_total"], 2)
        # may still use additional search parameters
        endpoint_url += "&review_state=closed"
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200, response.content)
        resp_json = response.json()
        self.assertEqual(resp_json[u"items_total"], 1)
        self.assertEqual(resp_json[u"items"][0][u"review_state"], u"closed")

        # includes every data as well as extra formatted values
        self.assertTrue("date" in resp_json["items"][0])
        # AT/DX
        self.assertTrue("startDate" in resp_json["items"][0] or
                        "start_date" in resp_json["items"][0])
        self.assertTrue("notes" in resp_json["items"][0])
        self.assertEqual(
            resp_json["items"][0]["formatted_assembly"],
            u'<p>Mr Present, <strike>Mr Absent</strike>, Mr Present2</p>')
        self.assertEqual(resp_json["items"][0]["observations"]["data"],
                         pattern.format(IMG_BASE64_DATA))
        transaction.abort()

    def test_restapi_search_meetings_accepting_items(self):
        """ """
        cfg = self.meetingConfig
        endpoint_url = "{0}/@search?config_id={1}&type=meeting".format(
            self.portal_url, cfg.getId()
        )

        # create 2 meetings
        self.changeUser("pmManager")
        meeting = self.create("Meeting", date=datetime(2020, 5, 10))
        self.assertEqual(self.get_review_state(meeting), "created")
        meeting2 = self.create("Meeting", date=datetime(2020, 5, 17))
        self.closeMeeting(meeting2)
        self.assertEqual(self.get_review_state(meeting2), "closed")
        transaction.commit()
        # only meeting is accepting items
        self.assertEqual(
            [meeting.UID()], [brain.UID for brain in cfg.getMeetingsAcceptingItems()]
        )

        # both found by default
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()[u"items_total"], 2)
        endpoint_url += "&meetings_accepting_items=True"
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200, response.content)
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
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()[u"items_total"], 2)
        # as pmCreator1, only item1 found
        response = self.api_session.get(endpoint_url_pattern % "pmCreator1")
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()[u"items_total"], 1)
        self.assertEqual(response.json()["items"][0][u"UID"], item1.UID())
        # as pmCreator2, only item2 found
        response = self.api_session.get(endpoint_url_pattern % "pmCreator2")
        self.assertEqual(response.status_code, 200, response.content)
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
        # nothing found for now
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200, response.content)
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
        self.assertEqual(response.status_code, 200, response.content)
        json = response.json()
        # only 2 items found
        self.assertEqual(json[u"items_total"], 2)
        self.assertEqual(json[u"items"][0]["UID"], item_dev2_uid)
        self.assertEqual(json[u"items"][1]["UID"], item_ven1_uid)
        # possible to complete the query with arbitray parameters
        # restrict only developers_uid
        endpoint_url += "&getProposingGroup={0}".format(self.developers_uid)
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200, response.content)
        json = response.json()
        # only 1 item found
        self.assertEqual(json[u"items_total"], 1)
        self.assertEqual(json[u"items"][0]["UID"], item_dev2_uid)
        # override Creator, use pmCreator1
        endpoint_url += "&Creator=pmCreator1"
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200, response.content)
        json = response.json()
        self.assertEqual(json[u"items_total"], 1)
        self.assertEqual(json[u"items"][0]["UID"], item_dev1_uid)
        # get items from pmManager and pmCreator1
        endpoint_url += "&Creator=pmManager"
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200, response.content)
        json = response.json()
        self.assertEqual(json[u"items_total"], 2)
        self.assertEqual(json[u"items"][0]["UID"], item_dev1_uid)
        self.assertEqual(json[u"items"][1]["UID"], item_dev2_uid)

    def test_restapi_search_without_config_id(self):
        """@search parameter config_id will ease searching but
           when not provided, then default @search functionnality is available."""
        self.changeUser("pmManager")
        endpoint_url = (
            "{0}/@search?portal_type=organization".format(self.portal_url)
        )
        transaction.commit()
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200, response.content)
        # organizations are returned
        json = response.json()
        for result in json[u"items"]:
            self.assertEqual(result[u'@type'], 'organization')
        transaction.abort()

    def test_restapi_search_without_type(self):
        """The @search endpoint original behavior is still useable."""
        cfg = self.meetingConfig
        self.changeUser("pmManager")
        endpoint_url = (
            "{0}/@search?UID={1}".format(self.portal_url, cfg.UID())
        )
        transaction.commit()
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200, response.content)
        json = response.json()
        self.assertEqual(json[u"items_total"], 1)
        self.assertEqual(json[u"items"][0][u'id'], cfg.getId())

    def test_restapi_search_fullobjects_and_includes(self):
        """Several includes may be passed as parameter when "fullobjects" is used.
           By default, "fullobjects" behavior is like in plone.restapi, it retuens every infos.
           But we may pass additional includes:
           - include_all: when set to false, nothing else but base data (id, uid, ...) are returned;
           - include_base_data: will include base data like id, uid, review_state, ...;
           - include_components: will include the "@components" section;
           - include_nextprev: will include next/previous infos;
           - include_parent: will serialize parent into "parent" key;
           - include_items: will include the contained elements;
           - include_target_url: will include the "targetUrl";
           - include_allow_discussion: will include infos about discussion;
           - additional_values: will include given additional values.
        """
        # create 1 item
        self.changeUser("pmManager")
        self.create("MeetingItem")
        transaction.commit()

        endpoint_url = "{0}/@search?config_id={1}&fullobjects=True".format(
            self.portal_url, self.meetingConfig.getId()
        )
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200, response.content)
        resp_json = response.json()
        self.assertEqual(resp_json[u"items_total"], 1)
        # by default everything is there, except "items" that is False by default
        self.assertTrue("@components" in resp_json["items"][0])
        self.assertTrue("id" in resp_json["items"][0])
        self.assertTrue("UID" in resp_json["items"][0])
        self.assertTrue("next_item" in resp_json["items"][0])
        self.assertTrue("previous_item" in resp_json["items"][0])
        self.assertTrue("parent" in resp_json["items"][0])
        self.assertTrue("allow_discussion" in resp_json["items"][0])
        self.assertTrue("layout" in resp_json["items"][0])
        self.assertTrue("formatted_itemNumber" in resp_json["items"][0])
        self.assertFalse("items" in resp_json["items"][0])
        # we may get what we want, only get "@components"
        endpoint_url = "{0}/@search?config_id={1}&fullobjects=True" \
            "&include_base_data=false&additional_values=" \
            "&include_all=false&include_components=true".format(
                self.portal_url, self.meetingConfig.getId())
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200, response.content)
        resp_json = response.json()
        self.assertEqual(resp_json[u"items_total"], 1)
        self.assertTrue("@components" in resp_json["items"][0])
        self.assertFalse("id" in resp_json["items"][0])
        self.assertFalse("UID" in resp_json["items"][0])
        self.assertFalse("next_item" in resp_json["items"][0])
        self.assertFalse("previous_item" in resp_json["items"][0])
        self.assertFalse("parent" in resp_json["items"][0])
        self.assertFalse("allow_discussion" in resp_json["items"][0])
        self.assertFalse("formatted_itemNumber" in resp_json["items"][0])
        self.assertFalse("items" in resp_json["items"][0])

    def test_restapi_search_extra_includes_parameters(self):
        """Every parameters may be passed to extra_includes:
           Example: extra_include=category, enable fullobjects and include_all=true:
           Parameters would be the following:
           - extra_include=category;
           - extra_include_category_fullobjects;
           - extra_include_category_include_all=false.
        """
        cfg = self.meetingConfig
        cfg.setUseGroupsAsCategories(False)
        # create 2 items
        self.changeUser("pmManager")
        self.create("MeetingItem")
        transaction.commit()

        endpoint_url = "{0}/@search?config_id={1}&extra_include=category" \
            "&extra_include_category_fullobjects" \
            "&extra_include_category_include_components=true" \
            "&extra_include_category_include_all=false".format(
                self.portal_url, self.meetingConfig.getId())
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200, response.content)
        resp_json = response.json()
        # we get @components and base data
        self.assertEqual(sorted(resp_json["items"][0]["extra_include_category"].keys()),
                         [u'@components',
                          u'@id',
                          u'@type',
                          u'UID',
                          u'created',
                          u'id',
                          u'is_folderish',
                          u'modified',
                          u'review_state',
                          u'title'])

    def test_restapi_search_metadata_fields(self):
        """metadata_fields may be used:
           - without fullobjects, the metadata catalog is used;
           - with fullobjects, then it is used to select the fields we want.
        """
        cfg = self.meetingConfig
        cfg.setUseGroupsAsCategories(False)
        # create 2 items
        self.changeUser("pmManager")
        self.create("MeetingItem")
        transaction.commit()

        # get item base data + getItemNumber and category enabled and category_id
        endpoint_url = "{0}/@search?config_id={1}" \
            "&metadata_fields=getItemNumber" \
            "&extra_include=category" \
            "&extra_include_category_fullobjects" \
            "&extra_include_category_include_all=false" \
            "&extra_include_category_include_base_data=false" \
            "&extra_include_category_metadata_fields=enabled" \
            "&extra_include_category_metadata_fields=category_id".format(
                self.portal_url, self.meetingConfig.getId())
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200, response.content)
        resp_json = response.json()
        # item
        self.assertEqual(sorted(resp_json["items"][0].keys()),
                         [u'@id', u'@type', u'UID', u'created', u'description',
                          u'enabled', u'extra_include_category', u'getItemNumber',
                          u'id', u'modified', u'review_state', u'title'])
        self.assertEqual(resp_json["items"][0]["getItemNumber"], 0)
        # category
        self.assertEqual(resp_json["items"][0]["extra_include_category"],
                         {u'category_id': u'development', u'enabled': True})

    def test_restapi_search_not_found_brain(self):
        """Check that everything is behaving correctly when some brains
        are lost in portal_catalog (object does not exist anymore)."""
        self.changeUser("pmManager")
        item1 = self.create("MeetingItem")
        item1_uid = item1.UID()
        item2 = self.create("MeetingItem")
        # prevent unindex when deleting item1
        old__unindexObject = MeetingItem.unindexObject
        MeetingItem.unindexObject = lambda *args: None
        self.deleteAsManager(item1_uid)
        MeetingItem.unindexObject = old__unindexObject
        self.assertTrue(self.catalog(UID=item1_uid))
        self.assertFalse(item1 in item1.aq_parent.objectValues())
        self.assertTrue(item2 in item1.aq_parent.objectValues())
        transaction.commit()

        # when using brains, 2 results
        endpoint_url = "{0}/@search?config_id={1}&sort_on=getId".format(
            self.portal_url, self.meetingConfig.getId())
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200, response.content)
        resp_json = response.json()
        self.assertEqual(len(resp_json["items"]), 2)
        # with fullobjects, only 1 result
        endpoint_url += "&fullobjects"
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200, response.content)
        resp_json = response.json()
        self.assertEqual(len(resp_json["items"]), 1)

    def test_restapi_search_data_are_anonymized(self):
        """Data collected from PloneMeeting are anonymized."""
        self._enableField("observations")
        self._enableField("observations", related_to="Meeting")

        # create 2 items
        text = '<p>Text shown<span class="pm-anonymize"> text hidden</span> and ' \
            'some <span class="highlight-red">highlighted text</span>.</p>'
        anonymized_text = '<p>Text shown<span class="pm-anonymize"></span> and ' \
            'some <span class="highlight-red">highlighted text</span>.</p>'
        self.changeUser("pmManager")
        item = self.create("MeetingItem")
        item.setObservations(text)
        item.setDecision(text)
        # in 4.1.x item observations was only readable until validated...
        self.validateItem(item)
        meeting = self.create("Meeting", date=datetime(2020, 6, 8, 8, 0))
        if HAS_MEETING_DX:
            meeting.observations = richtextval(text)
        else:
            meeting.setObservations(text)
        transaction.commit()

        # query to get meeting and item description
        endpoint_url = "{0}/@search?fullobjects" \
            "&include_all=false" \
            "&extra_include=public_deliberation" \
            "&metadata_fields=observations" \
            "&UID={2}&UID={3}&sort_on=getId".format(
                self.portal_url, self.meetingConfig.getId(),
                item.UID(), meeting.UID())
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200, response.content)
        resp_json = response.json()
        self.assertEqual(resp_json["items_total"], 2)
        # item
        # RichTextField
        self.assertEqual(resp_json["items"][0]["observations"]["data"], anonymized_text)
        # RichText treated by printXhtml
        self.assertEqual(
            resp_json["items"][0]["extra_include_deliberation"]["public_deliberation"],
            anonymized_text)
        # meeting
        # RichTextField
        self.assertEqual(resp_json["items"][1]["observations"]["data"], anonymized_text)


def test_suite():
    from unittest import TestSuite, makeSuite

    suite = TestSuite()
    # add a prefix to avoid every PM tests to be executed
    suite.addTest(makeSuite(testServiceSearch, prefix="test_restapi_"))
    return suite
