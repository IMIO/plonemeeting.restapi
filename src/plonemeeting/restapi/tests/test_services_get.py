# -*- coding: utf-8 -*-

from datetime import datetime
from plonemeeting.restapi.serializer.meeting import HAS_MEETING_DX
from plonemeeting.restapi.services.get import UID_NOT_ACCESSIBLE_ERROR
from plonemeeting.restapi.services.get import UID_NOT_FOUND_ERROR
from plonemeeting.restapi.services.get import UID_REQUIRED_ERROR
from plonemeeting.restapi.services.get import UID_WRONG_TYPE_ERROR
from plonemeeting.restapi.tests.base import BaseTestCase
from Products.PloneMeeting.tests.PloneMeetingTestCase import DEFAULT_USER_PASSWORD

import transaction


class testServiceGetUid(BaseTestCase):
    """@get endpoint, let's get element based on UID."""

    def setUp(self):
        """ """
        super(testServiceGetUid, self).setUp()
        self.changeUser("pmManager")
        self.item1 = self.create("MeetingItem", proposingGroup=self.developers_uid)
        self.item1_uid = self.item1.UID()
        self.item2 = self.create("MeetingItem", proposingGroup=self.vendors_uid)
        self.item2_uid = self.item2.UID()
        self.meeting = self.create("Meeting", date=datetime(2021, 9, 23, 10, 0))
        self.meeting_uid = self.meeting.UID()
        transaction.commit()

    def tearDown(self):
        self.api_session.close()
        transaction.abort()

    def test_restapi_get_uid_required(self):
        """The 'UID' or 'uid' parameter must be given"""
        endpoint_url = "{0}/@get".format(self.portal_url)
        response = self.api_session.get(endpoint_url)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.json(), {u"message": UID_REQUIRED_ERROR, u"type": u"Exception"}
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
        # passing an extra_include will work and still use summary
        endpoint_url += "&extra_include=proposing_group"
        response = self.api_session.get(endpoint_url)
        json = response.json()
        self.assertEqual(
            sorted(json.keys()),
            [u'@extra_includes', u'@id', u'@type', u'UID', u'created',
             u'description', u'enabled', u'extra_include_proposing_group',
             u'id', u'modified', u'review_state', u'title'])
        # fullobject is possible too
        endpoint_url += "&fullobjects"
        response = self.api_session.get(endpoint_url)
        json = response.json()
        self.assertTrue("extra_include_proposing_group" in json)
        self.assertTrue("externalIdentifier" in json)
        self.assertTrue("itemReference" in json)

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
        self.addAnnex(self.item1)

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


def test_suite():
    from unittest import TestSuite, makeSuite

    suite = TestSuite()
    # add a prefix to avoid every PM tests to be executed
    suite.addTest(makeSuite(testServiceGetUid, prefix="test_restapi_"))
    return suite
