# -*- coding: utf-8 -*-

from datetime import datetime
from DateTime import DateTime
from plonemeeting.restapi.config import IN_NAME_OF_UNAUTHORIZED
from plonemeeting.restapi.serializer.meeting import HAS_MEETING_DX
from plonemeeting.restapi.services.get import UID_REQUIRED_ERROR
from plonemeeting.restapi.services.get import UID_WRONG_TYPE_ERROR
from plonemeeting.restapi.tests.base import BaseTestCase
from plonemeeting.restapi.utils import IN_NAME_OF_CONFIG_ID_ERROR
from plonemeeting.restapi.utils import UID_NOT_ACCESSIBLE_ERROR
from plonemeeting.restapi.utils import UID_NOT_FOUND_ERROR
from Products.PloneMeeting.tests.PloneMeetingTestCase import DEFAULT_USER_PASSWORD

import transaction
import unittest


class testServiceGetUid(BaseTestCase):
    """@get endpoint, let's get element based on UID."""

    def setUp(self):
        """ """
        super(testServiceGetUid, self).setUp()
        # especially necessary for branch 4.1.x where proposingGroup/category
        # was mixed and MeetingItem.getCategory would return the proposingGroup or the category
        self.meetingConfig.setUseGroupsAsCategories(False)
        self.changeUser("pmManager")
        self.item1 = self.create("MeetingItem", proposingGroup=self.developers_uid)
        self.item1_uid = self.item1.UID()
        self.item2 = self.create("MeetingItem", proposingGroup=self.vendors_uid)
        self.item2_uid = self.item2.UID()
        if HAS_MEETING_DX:
            self.meeting = self.create("Meeting", date=datetime(2021, 9, 23, 10, 0))
        else:
            self.meeting = self.create("Meeting", date=DateTime('2021/09/23 10:0'))
        self.meeting_uid = self.meeting.UID()
        transaction.commit()

    def tearDown(self):
        self.api_session.close()
        transaction.abort()

    def test_restapi_get_uid_required(self):
        """The 'UID' or 'uid' parameter must be given"""
        endpoint_url = "{0}/@get".format(self.portal_url)
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(), {u"message": UID_REQUIRED_ERROR, u"type": u"BadRequest"}
        )
        endpoint_url += "?UID={0}".format(self.item1_uid)
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200, response.content)

    def test_restapi_get_uid_not_found(self):
        """When given UID does not exist"""
        endpoint_url = "{0}/@get?UID=unknown".format(self.portal_url)
        response = self.api_session.get(endpoint_url)
        self.assertEqual(
            response.json(),
            {u"message": UID_NOT_FOUND_ERROR % "unknown", u"type": u"BadRequest"},
        )

    def test_restapi_get_uid_not_accessible(self):
        """When given UID exists but current user can not access it"""
        endpoint_url = "{0}/@get?UID={1}".format(self.portal_url, self.item2_uid)
        # pmCreator1 can not access item with proposingGroup 'vendors'
        self.api_session.auth = ("pmCreator1", DEFAULT_USER_PASSWORD)
        response = self.api_session.get(endpoint_url)
        self.assertEqual(
            response.json(),
            {
                u"message": UID_NOT_ACCESSIBLE_ERROR % (self.item2_uid, "pmCreator1"),
                u"type": u"BadRequest",
            },
        )

    def _check_get_uid_endpoint(self, obj, endpoint_name="@get"):
        """ """
        obj_uid = obj.UID()
        endpoint_url = "{0}/{1}?UID={2}".format(
            self.portal_url, endpoint_name, obj_uid
        )
        response = self.api_session.get(endpoint_url)
        json = response.json()
        self.assertEqual(json["id"], obj.getId())
        self.assertEqual(json["UID"], obj_uid)
        # by default, no items
        # except for AT Meeting for which items is also a ReferenceField...
        if (obj.__class__.__name__ == "Meeting" and HAS_MEETING_DX) or \
           obj.__class__.__name__ != "Meeting":
            self.assertFalse("items" in json)

    def test_restapi_get_uid(self):
        """When given UID is accessible, it is returned"""
        self._check_get_uid_endpoint(obj=self.item1)

    def test_restapi_get_uid_item(self):
        """There is a @item convenience endpoint that is just a shortcut to @get"""
        self._check_get_uid_endpoint(obj=self.item1, endpoint_name="@item")

    def test_restapi_get_uid_item_wrong_type(self):
        """@item endpoint is supposed to return an item, so if we receive an UID
           of another type, we raise"""
        endpoint_url = "{0}/@item?UID={1}".format(
            self.portal_url, self.portal.Members.pmManager.UID()
        )
        response = self.api_session.get(endpoint_url)
        self.assertEqual(
            response.json(), {u"message": UID_WRONG_TYPE_ERROR, u"type": u"BadRequest"}
        )

    def test_restapi_get_uid_meeting(self):
        """There is a @meeting convenience endpoint that is just a shortcut to @get"""
        self._check_get_uid_endpoint(obj=self.meeting, endpoint_name="@meeting")

    def test_restapi_get_uid_meeting_wrong_type(self):
        """@meeting endpoint is supposed to return a meeting, so if we receive an UID
           of another type, we raise"""
        endpoint_url = "{0}/@meeting?UID={1}".format(
            self.portal_url, self.portal.Members.pmManager.UID()
        )
        response = self.api_session.get(endpoint_url)
        self.assertEqual(
            response.json(), {u"message": UID_WRONG_TYPE_ERROR, u"type": u"BadRequest"}
        )

    def test_restapi_get_uid_fullobjects(self):
        """By default summary is returned except when "fullobject" is given"""
        endpoint_url = "{0}/@get?UID={1}".format(
            self.portal_url, self.item1_uid
        )
        response = self.api_session.get(endpoint_url)
        json = response.json()
        # summary data
        self.assertEqual(
            sorted(json.keys()),
            [u'@extra_includes', u'@id', u'@type', u'UID', u'created',
             u'description', u'enabled', u'id',
             u'modified', u'review_state', u'title'])
        # passing an extra_include will make it use the fullobjects serializer
        endpoint_url += "&extra_include=proposing_group"
        response = self.api_session.get(endpoint_url)
        json = response.json()
        self.assertEqual(
            sorted(json.keys()),
            [u'@extra_includes', u'@id', u'@type', u'UID', u'created',
             u'extra_include_proposing_group', u'id', u'modified',
             u'review_state', u'title'])
        # fullobject is possible too
        endpoint_url += "&fullobjects"
        response = self.api_session.get(endpoint_url)
        json = response.json()
        self.assertTrue("extra_include_proposing_group" in json)
        self.assertTrue("externalIdentifier" in json)
        self.assertTrue("itemReference" in json)

    def test_restapi_get_uid_in_name_of(self):
        """Check when using parameter in_name_of"""
        endpoint_url = "{0}/@get?UID={1}&in_name_of=pmCreator1".format(
            self.portal_url, self.item1_uid
        )
        response = self.api_session.get(endpoint_url)
        # config_id is required when using in_name_of
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(), {u"message": IN_NAME_OF_CONFIG_ID_ERROR, u"type": u"BadRequest"}
        )
        # with config_id the element is correctly returned
        endpoint_url += "&config_id=%s" % self.meetingConfig.getId()
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()["UID"], self.item1_uid)
        # try to get an inaccessible element
        endpoint_url = endpoint_url.replace(self.item1_uid, self.item2_uid)
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {
                u"message": UID_NOT_ACCESSIBLE_ERROR % (self.item2_uid, "pmCreator1"),
                u"type": u"BadRequest",
            },
        )
        # must be MeetingManager to use in_name_of
        self.api_session.auth = ("pmCreator1", DEFAULT_USER_PASSWORD)
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.json(),
            {
                u"message": IN_NAME_OF_UNAUTHORIZED % "pmCreator1",
                u"type": u"Unauthorized",
            },
        )

    def test_restapi_get_uid_extra_include_pod_templates(self):
        """Test the extra_include=pod_templates."""
        # MeetingItem
        endpoint_url = "{0}/@get?UID={1}&extra_include=pod_templates".format(
            self.portal_url, self.item1_uid
        )
        response = self.api_session.get(endpoint_url)
        json = response.json()
        item_pod_template_json = json["extra_include_pod_templates"][0]
        self.assertEqual(item_pod_template_json[u'@type'], u'ConfigurablePODTemplate')
        self.assertEqual(item_pod_template_json[u'id'], u'itemTemplate')
        self.assertEqual(item_pod_template_json[u'outputs'][0][u'format'], u'odt')
        # Meeting
        endpoint_url = "{0}/@get?UID={1}&extra_include=pod_templates".format(
            self.portal_url, self.meeting_uid
        )
        response = self.api_session.get(endpoint_url)
        json = response.json()
        meeting_pod_template_json = json["extra_include_pod_templates"][0]
        self.assertEqual(meeting_pod_template_json[u'@type'], u'ConfigurablePODTemplate')
        self.assertEqual(meeting_pod_template_json[u'id'], u'agendaTemplate')
        self.assertEqual(meeting_pod_template_json[u'outputs'][0][u'format'], u'odt')

    def test_restapi_get_uid_extra_include_annexes(self):
        """Test the extra_include=annexes."""
        # configure item1 and meeting
        self._enable_annex_config(self.item1, param="publishable")
        self._enable_annex_config(self.meeting, param="publishable")
        # MetingItem
        item_annex = self.addAnnex(self.item1, publishable=True)
        # add a second annex but it will not be retrieved
        self.addAnnex(self.item1)
        # Meeting
        meeting_annex = self.addAnnex(self.meeting, publishable=True)
        # add a second annex but it will not be retrieved
        self.addAnnex(self.meeting)

        # MeetingItem, just get the publishable annexes and include file
        endpoint_url_pattern = "{0}/@get?UID={1}&extra_include=annexes" \
            "&extra_include_annexes_fullobjects" \
            "&extra_include_annexes_publishable=true" \
            "&extra_include_annexes_metadata_fields=file"
        endpoint_url = endpoint_url_pattern.format(
            self.portal_url, self.item1_uid
        )
        response = self.api_session.get(endpoint_url)
        json = response.json()
        item_annexes_json = json["extra_include_annexes"]
        self.assertEqual(len(item_annexes_json), 1)
        self.assertEqual(item_annexes_json[0][u'@type'], u'annex')
        self.assertEqual(item_annexes_json[0][u'UID'], item_annex.UID())
        self.assertEqual(item_annexes_json[0][u'file'][u'filename'], u'FILE.txt')

        # Meeting
        endpoint_url = endpoint_url_pattern.format(
            self.portal_url, self.meeting_uid
        )
        response = self.api_session.get(endpoint_url)
        json = response.json()
        meeting_annexes_json = json["extra_include_annexes"]
        self.assertEqual(len(meeting_annexes_json), 1)
        self.assertEqual(meeting_annexes_json[0][u'@type'], u'annex')
        self.assertEqual(meeting_annexes_json[0][u'UID'], meeting_annex.UID())
        self.assertEqual(meeting_annexes_json[0][u'file'][u'filename'], u'FILE.txt')

        # getting item or meeting annexes without fullobjects also includes
        # the annex file as annex file is returned in any case
        endpoint_url_pattern = "{0}/@get?UID={1}&extra_include=annexes"
        endpoint_url = endpoint_url_pattern.format(
            self.portal_url, self.item1_uid
        )
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 200, response.content)
        json = response.json()
        item_annexes_json = json["extra_include_annexes"]
        self.assertEqual(len(item_annexes_json), 2)
        self.assertEqual(item_annexes_json[0][u'@type'], u'annex')
        self.assertEqual(item_annexes_json[0][u'UID'], item_annex.UID())
        self.assertEqual(item_annexes_json[0][u'file'][u'filename'], u'FILE.txt')

    @unittest.skipIf(not HAS_MEETING_DX, "linked_items only works with PloneMeeting 4.2+")  # noqa
    def test_restapi_get_uid_extra_include_linked_items(self):
        """Test the extra_include=linked_items."""
        cfg = self.meetingConfig
        self._removeConfigObjectsFor(cfg)
        cfg.setItemManualSentToOtherMCStates(('itemcreated', ))
        cfg2 = self.meetingConfig2
        cfg2Id = cfg2.getId()
        # setup, create item, delay it, send it to cfg2
        # auto linked items
        self.changeUser('pmManager')
        item = self.create('MeetingItem', decision=self.decisionText)
        item_uid = item.UID()
        meeting = self.create('Meeting')
        self.presentItem(item)
        self.decideMeeting(meeting)
        self.do(item, 'delay')
        new_item = item.get_successors()[0]
        new_item_uid = new_item.UID()
        new_item.setOtherMeetingConfigsClonableTo((cfg2Id, ))
        cfg2_item = new_item.cloneToOtherMeetingConfig(cfg2Id)
        cfg2_item_uid = cfg2_item.UID()
        # set manually linked items
        item2 = self.create('MeetingItem', decision=self.decisionText)
        item2_uid = item2.UID()
        item3 = self.create('MeetingItem', decision=self.decisionText)
        item3_uid = item3.UID()
        item.setManuallyLinkedItems((item2.UID(), item3.UID()))
        transaction.commit()

        # by default we get the auto linked items
        endpoint_url_pattern = "{0}/@get?UID={1}&extra_include=linked_items"
        endpoint_url = endpoint_url_pattern.format(self.portal_url, item_uid)
        response = self.api_session.get(endpoint_url)
        json = response.json()
        self.assertEqual(json['extra_include_linked_items_items_total'], 2)
        self.assertEqual(
            [linked_item['UID'] for linked_item in json["extra_include_linked_items"]],
            [new_item_uid, cfg2_item_uid])
        # we may filter values, for example get only the cfg2 item
        filter_endpoint_url = endpoint_url + "&extra_include_linked_items_filter=portal_type|{0}".format(
            cfg2.getItemTypeName())
        response = self.api_session.get(filter_endpoint_url)
        json = response.json()
        self.assertEqual(json['extra_include_linked_items_items_total'], 1)
        self.assertEqual(
            [linked_item['UID'] for linked_item in json["extra_include_linked_items"]],
            [cfg2_item_uid])
        # several filters, filter may be a callable method, here "query_state"
        filter_endpoint_url = filter_endpoint_url + "&extra_include_linked_items_filter=query_state|{0}".format(
            cfg2_item.query_state())
        response = self.api_session.get(filter_endpoint_url)
        json = response.json()
        self.assertEqual(json['extra_include_linked_items_items_total'], 1)
        self.assertEqual(
            [linked_item['UID'] for linked_item in json["extra_include_linked_items"]],
            [cfg2_item_uid])

        # we may ask specific linked items: "manual", "predecessor",
        # "predecessors", "successors" and every_successors"
        # manual
        endpoint_url += "&extra_include_linked_items_mode=manual"
        response = self.api_session.get(endpoint_url)
        json = response.json()
        self.assertEqual(json['extra_include_linked_items_items_total'], 2)
        self.assertEqual(
            [linked_item['UID'] for linked_item in json["extra_include_linked_items"]],
            [item2_uid, item3_uid])
        # predecessor, no predecessor for item
        endpoint_url = endpoint_url.replace("manual", "predecessor")
        response = self.api_session.get(endpoint_url)
        json = response.json()
        self.assertEqual(json['extra_include_linked_items_items_total'], 0)
        self.assertEqual(json["extra_include_linked_items"], [])
        # get predecessor for cfg2_item
        endpoint_url = endpoint_url.replace(item_uid, cfg2_item_uid)
        response = self.api_session.get(endpoint_url)
        json = response.json()
        self.assertEqual(json['extra_include_linked_items_items_total'], 1)
        self.assertEqual(
            [linked_item['UID'] for linked_item in json["extra_include_linked_items"]],
            [new_item_uid])
        # predecessors
        endpoint_url = endpoint_url.replace("predecessor", "predecessors")
        response = self.api_session.get(endpoint_url)
        json = response.json()
        self.assertEqual(json['extra_include_linked_items_items_total'], 2)
        self.assertEqual(
            [linked_item['UID'] for linked_item in json["extra_include_linked_items"]],
            [item_uid, new_item_uid])
        # successors, no successors for cfg2_item
        endpoint_url = endpoint_url.replace("predecessors", "successors")
        response = self.api_session.get(endpoint_url)
        json = response.json()
        self.assertEqual(json['extra_include_linked_items_items_total'], 0)
        self.assertEqual(json["extra_include_linked_items"], [])
        # get successors for item
        endpoint_url = endpoint_url.replace(cfg2_item_uid, item_uid)
        response = self.api_session.get(endpoint_url)
        json = response.json()
        self.assertEqual(json['extra_include_linked_items_items_total'], 1)
        self.assertEqual(
            [linked_item['UID'] for linked_item in json["extra_include_linked_items"]],
            [new_item_uid])
        # every_successors
        endpoint_url = endpoint_url.replace("successors", "every_successors")
        response = self.api_session.get(endpoint_url)
        json = response.json()
        self.assertEqual(json['extra_include_linked_items_items_total'], 2)
        self.assertEqual(
            [linked_item['UID'] for linked_item in json["extra_include_linked_items"]],
            [new_item_uid, cfg2_item_uid])
        # the extra_include_linked_items_fullobjects works as well, by default we get the summary
        self.assertFalse('proposingGroup' in json["extra_include_linked_items"][0])
        endpoint_url += "&extra_include_linked_items_fullobjects"
        response = self.api_session.get(endpoint_url)
        json = response.json()
        self.assertTrue('proposingGroup' in json["extra_include_linked_items"][0])

    def test_restapi_get_uid_include_choices_for(self):
        """Test parameter include_choices_for that receives a list of field names
           and will append the related vocabulary values to the response."""
        # MeetingItem + include_choices on organization (DX)
        endpoint_url_pattern = "{0}/@get?UID={1}&include_choices_for=category" \
            "&include_choices_for=associatedGroups" \
            "&include_choices_for=title" \
            "&extra_include=proposing_group" \
            "&extra_include_proposing_group_include_choices_for=item_advice_states" \
            "&extra_include_proposing_group_include_choices_for=organization_type"

        endpoint_url = endpoint_url_pattern.format(
            self.portal_url, self.item1_uid)
        response = self.api_session.get(endpoint_url)
        json = response.json()
        self.assertEqual([elt['token'] for elt in json["category__choices"]],
                         [u'development', u'events', u'research'])
        self.assertEqual([elt['title'] for elt in json["associatedGroups__choices"]],
                         [u'Developers', u'Vendors'])
        # fields that do not have a vocabulary are ignored
        self.assertFalse("title__choices" in json)
        # field organization.item_advice_states is not readable so not returned
        self.assertFalse("item_advice_states__choices" in
                         json["extra_include_proposing_group"])
        # but field organization_type is readable so included
        self.assertEqual(
            json["extra_include_proposing_group"]["organization_type__choices"],
            [{u'token': u'default', u'title': u'D\xe9faut'}])

        # query the MeetingConfig (include_choices on an AT)
        endpoint_url_pattern = "{0}/@get?UID={1}&include_choices_for=usedItemAttributes"
        endpoint_url = endpoint_url_pattern.format(
            self.portal_url, self.meetingConfig.UID())
        response = self.api_session.get(endpoint_url)
        json = response.json()
        self.assertTrue(
            {u'title': u'Description (description)', u'token': u'description'}
            in json["usedItemAttributes__choices"])
        self.assertTrue(
            {u'title': u'Classifier (classifier)', u'token': u'classifier'}
            in json["usedItemAttributes__choices"])
        self.assertTrue(
            {u'title': u'Checklist (textCheckList)', u'token': u'textCheckList'}
            in json["usedItemAttributes__choices"])


def test_suite():
    from unittest import TestSuite, makeSuite

    suite = TestSuite()
    # add a prefix to avoid every PM tests to be executed
    suite.addTest(makeSuite(testServiceGetUid, prefix="test_restapi_"))
    return suite
