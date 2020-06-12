# -*- coding: utf-8 -*-

from collective.iconifiedcategory.utils import calculate_category_id
from plonemeeting.restapi.config import CONFIG_ID_ERROR
from plonemeeting.restapi.config import CONFIG_ID_NOT_FOUND_ERROR
from plonemeeting.restapi.config import IN_NAME_OF_UNAUTHORIZED
from plonemeeting.restapi.services.add import ANNEX_CONTENT_CATEGORY_ERROR
from plonemeeting.restapi.services.add import OPTIONAL_FIELD_ERROR
from plonemeeting.restapi.testing import PM_REST_TEST_ADD_PROFILE_FUNCTIONAL
from plonemeeting.restapi.tests.base import BaseTestCase
from plonemeeting.restapi.tests.config import base64_pdf_data
from plonemeeting.restapi.utils import IN_NAME_OF_USER_NOT_FOUND
from Products.PloneMeeting.tests.PloneMeetingTestCase import DEFAULT_USER_PASSWORD
from Products.PloneMeeting.utils import get_annexes

import transaction


class testServiceAddItem(BaseTestCase):
    """@item POST endpoint
       File is called test_services_zadd.py to be sure tests are executed
       last to avoid test isolation problems."""

    layer = PM_REST_TEST_ADD_PROFILE_FUNCTIONAL

    def tearDown(self):
        self.api_session.close()

    def test_restapi_add_item_config_id_not_found(self):
        """The 'config_id' parameter must be given"""
        endpoint_url = "{0}/@item".format(self.portal_url)
        response = self.api_session.post(
            endpoint_url,
            json={"config_id": "unknown"})
        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.json(),
            {u'message': CONFIG_ID_NOT_FOUND_ERROR % "unknown",
             u'type': u'Exception'})

    def test_restapi_add_item_required_params(self):
        """A valid 'config_id' must be given"""
        self.changeUser('pmManager')
        pmFolder = self.getMeetingFolder()
        self.assertEqual(len(pmFolder.objectIds('MeetingItem')), 0)
        endpoint_url = "{0}/@item".format(self.portal_url)
        response = self.api_session.post(endpoint_url)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json(),
                         {u'message': CONFIG_ID_ERROR,
                          u'type': u'Exception'})
        response = self.api_session.post(
            endpoint_url,
            json={"config_id": self.meetingConfig.getId(),
                  "proposingGroup": self.developers_uid,
                  "title": "My item"})
        self.assertEqual(response.status_code, 201)
        transaction.begin()
        pmFolder = self.getMeetingFolder()
        self.assertEqual(len(pmFolder.objectIds('MeetingItem')), 1)
        item = pmFolder.get('my-item')
        self.assertEqual(item.Title(), "My item")
        self.assertEqual(item.getProposingGroup(), self.developers_uid)
        transaction.abort()

    def test_restapi_add_item_optional_fields(self):
        """When creating an item, given optional fields must be enabled in config."""
        cfg = self.meetingConfig
        self.assertFalse('notes' in cfg.getUsedItemAttributes())
        self.changeUser('pmManager')
        endpoint_url = "{0}/@item".format(self.portal_url)
        json = {"config_id": cfg.getId(),
                "proposingGroup": self.developers_uid,
                "title": "My item",
                "notes": u"<p>My notes</p>"}
        response = self.api_session.post(endpoint_url, json=json)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(),
                         {u'message': OPTIONAL_FIELD_ERROR % "notes",
                          u'type': u'BadRequest'})
        self._enableField("notes")
        transaction.commit()
        response = self.api_session.post(endpoint_url, json=json)
        self.assertEqual(response.status_code, 201)
        transaction.commit()
        pmFolder = self.getMeetingFolder()
        item = pmFolder.objectValues()[-1]
        self.assertEqual(item.Title(), json['title'])
        self.assertEqual(item.getProposingGroup(), json['proposingGroup'])
        self.assertEqual(item.getNotes(), json['notes'])
        transaction.abort()

    def test_restapi_add_item_org_fields(self):
        """When creating an item, values for fields storing organization
           uids may receive organizations ids instead to ease use by externals."""
        cfg = self.meetingConfig
        cfg.setOrderedGroupsInCharge([self.vendors_uid])
        self._enableField("groupsInCharge")
        self._enableField("associatedGroups")
        transaction.commit()
        self.changeUser('pmManager')
        endpoint_url = "{0}/@item".format(self.portal_url)
        json = {"config_id": cfg.getId(),
                "proposingGroup": self.developers.getId(),
                "groupsInCharge": [self.vendors.getId(), self.developers.getId()],
                "associatedGroups": [self.vendors.getId(), self.developers.getId()],
                "optionalAdvisers": [self.vendors.getId()],
                "title": "My item"}
        response = self.api_session.post(endpoint_url, json=json)
        self.assertEqual(response.status_code, 201)
        transaction.commit()
        pmFolder = self.getMeetingFolder()
        item = pmFolder.objectValues()[-1]
        self.assertEqual(item.Title(), json['title'])
        # turned to UIDs
        self.assertEqual(item.getProposingGroup(), self.developers_uid)
        self.assertEqual(item.getGroupsInCharge(), [self.vendors_uid, self.developers_uid])
        self.assertEqual(item.getAssociatedGroups(), (self.vendors_uid, self.developers_uid))
        self.assertEqual(item.getOptionalAdvisers(), (self.vendors_uid, ))
        transaction.abort()

    def test_restapi_add_item_with_annexes(self):
        """When creating an item, we may add annexes as __children__."""
        cfg = self.meetingConfig
        self.changeUser('pmManager')
        endpoint_url = "{0}/@item".format(self.portal_url)
        json = {"config_id": cfg.getId(),
                "proposingGroup": self.developers.getId(),
                "title": "My item",
                "__children__": [
                    {
                        "@type": "annex",
                        "title": "My annex",
                        "content_category": "item-annex",
                        "file": {"data": "123456",
                                 "encoding": "ascii",
                                 "filename": "file.txt"},
                    }, ],
                }
        response = self.api_session.post(endpoint_url, json=json)
        self.assertEqual(response.status_code, 201)
        transaction.commit()
        pmFolder = self.getMeetingFolder()
        item = pmFolder.objectValues()[-1]
        self.assertEqual(item.Title(), json['title'])
        annex = get_annexes(item)[0]
        self.assertEqual(annex.title, json['__children__'][0]['title'])
        self.assertEqual(
            annex.content_category,
            calculate_category_id(cfg.annexes_types.item_annexes.get('item-annex')))
        self.assertEqual(annex.file.filename, json['__children__'][0]['file']['filename'])
        self.assertEqual(annex.file.size, 6)
        self.assertEqual(annex.file.contentType, 'text/plain')
        transaction.abort()

    def test_restapi_add_item_with_annexes_encoding(self):
        """When creating an item, we may add annexes as __children__,
           if encoding not given, we assume it is 'base64'."""
        cfg = self.meetingConfig
        self.changeUser('pmManager')
        endpoint_url = "{0}/@item".format(self.portal_url)
        json = {"config_id": cfg.getId(),
                "proposingGroup": self.developers.getId(),
                "title": "My item",
                "__children__": [
                    {
                        "@type": "annex",
                        "title": "My annex",
                        "content_category": "item-annex",
                        "file": {"data": base64_pdf_data,
                                 "filename": "file.pdf"},
                    }, ],
                }
        transaction.begin()
        response = self.api_session.post(endpoint_url, json=json)
        self.assertEqual(response.status_code, 201)
        transaction.commit()
        pmFolder = self.getMeetingFolder()
        item = pmFolder.objectValues()[-1]
        annex = get_annexes(item)[0]
        self.assertEqual(annex.file.filename, json['__children__'][0]['file']['filename'])
        self.assertEqual(annex.file.size, 6475)
        self.assertEqual(annex.file.contentType, 'application/pdf')

    def test_restapi_add_item_with_annexes_content_category(self):
        """When creating an item, we may add annexes as __children__,
           if using wrong content_category, cration is aborted."""
        cfg = self.meetingConfig
        self.changeUser('pmManager')
        endpoint_url = "{0}/@item".format(self.portal_url)
        json = {"config_id": cfg.getId(),
                "proposingGroup": self.developers.getId(),
                "title": "My item",
                "__children__": [
                    {
                        "@type": "annex",
                        "title": "My annex",
                        "content_category": "unknown",
                        "file": {"data": "123456",
                                 "encoding": "ascii",
                                 "filename": "file.txt"},
                    }, ],
                }
        response = self.api_session.post(endpoint_url, json=json)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(),
                         {u'message': ANNEX_CONTENT_CATEGORY_ERROR % "unknown",
                          u'type': u'BadRequest'})

    def test_restapi_add_item_with_annexes_filename_or_content_type_required(self):
        """When creating an item, we may add annexes as __children__,
           one of 'filename' or 'content-type' is required to determinate content_type."""
        cfg = self.meetingConfig
        self.changeUser('pmManager')
        endpoint_url = "{0}/@item".format(self.portal_url)
        json = {"config_id": cfg.getId(),
                "proposingGroup": self.developers.getId(),
                "title": "My item",
                "__children__": [
                    {
                        "@type": "annex",
                        "title": "My annex",
                        "content_category": "unknown",
                        "file": {"data": "123456",
                                 "encoding": "ascii",
                                 "filename": "file.txt"},
                    }, ],
                }
        response = self.api_session.post(endpoint_url, json=json)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(),
                         {u'message': ANNEX_CONTENT_CATEGORY_ERROR % "unknown",
                          u'type': u'BadRequest'})

    def test_restapi_add_item_with_several_annexes(self):
        """When creating an item, we may add annexes as __children__,
           we may add several annexes at once."""
        cfg = self.meetingConfig
        self.changeUser('pmManager')
        endpoint_url = "{0}/@item".format(self.portal_url)
        json = {"config_id": cfg.getId(),
                "proposingGroup": self.developers.getId(),
                "title": "My item",
                "__children__": [
                    {
                        "@type": "annex",
                        "title": "My annex 1",
                        "content_category": "item-annex",
                        "file": {"data": "123456",
                                 "encoding": "ascii",
                                 "filename": "file.txt"},
                    },
                    {
                        "@type": "annex",
                        "title": "My annex 2",
                        "content_category": "item-annex",
                        "file": {"data": base64_pdf_data,
                                 "filename": "file.pdf"},
                    }, ],
                }
        response = self.api_session.post(endpoint_url, json=json)
        self.assertEqual(response.status_code, 201)
        transaction.begin()
        pmFolder = self.getMeetingFolder()
        item = pmFolder.objectValues()[-1]
        annex1 = get_annexes(item)[0]
        annex2 = get_annexes(item)[1]
        self.assertEqual(annex1.file.filename, json['__children__'][0]['file']['filename'])
        self.assertEqual(annex1.file.size, 6)
        self.assertEqual(annex1.file.contentType, 'text/plain')
        self.assertEqual(annex2.file.filename, json['__children__'][1]['file']['filename'])
        self.assertEqual(annex2.file.size, 6475)
        self.assertEqual(annex2.file.contentType, 'application/pdf')
        transaction.abort()

    def test_restapi_add_item_in_name_of(self):
        """Test while using 'in_name_of' parameter"""
        cfg = self.meetingConfig
        # must be (Meeting)Manager to use in_name_of
        self.api_session.auth = ('pmCreator1', DEFAULT_USER_PASSWORD)
        endpoint_url = "{0}/@item".format(self.portal_url)
        json = {"config_id": cfg.getId(),
                "proposingGroup": self.vendors_uid,
                "title": "My item",
                "in_name_of": "pmCreator2"}
        response = self.api_session.post(endpoint_url, json=json)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(),
                         {u'message': IN_NAME_OF_UNAUTHORIZED % "pmCreator2",
                          u'type': u'Unauthorized'})
        # user must exist
        self.api_session.auth = ('pmManager', DEFAULT_USER_PASSWORD)
        json["in_name_of"] = "unknown"
        response = self.api_session.post(endpoint_url, json=json)
        self.assertEqual(response.json(),
                         {u'message': IN_NAME_OF_USER_NOT_FOUND % "unknown",
                          u'type': u'BadRequest'})
        # now as MeetingManager for pmCreator2
        json["in_name_of"] = "pmCreator2"
        response = self.api_session.post(endpoint_url, json=json)
        self.assertEqual(response.status_code, 201)
        # item was created in the pmCreator2 folder
        response_json = response.json()
        self.assertEqual(response_json['creators'], [u'pmCreator2'])
        self.assertTrue('Members/pmCreator2/mymeetings' in response_json['@id'])


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    # add a prefix to avoid every PM tests to be executed
    suite.addTest(makeSuite(testServiceAddItem, prefix='test_restapi_'))
    return suite
