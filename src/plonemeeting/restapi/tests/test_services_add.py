# -*- coding: utf-8 -*-

from collective.iconifiedcategory.utils import calculate_category_id
from datetime import datetime
from datetime import timedelta
from DateTime import DateTime
from imio.helpers.content import object_values
from plonemeeting.restapi.config import CONFIG_ID_ERROR
from plonemeeting.restapi.config import CONFIG_ID_NOT_FOUND_ERROR
from plonemeeting.restapi.config import IN_NAME_OF_UNAUTHORIZED
from plonemeeting.restapi.serializer.meeting import HAS_MEETING_DX
from plonemeeting.restapi.services.add import ANNEX_CONTENT_CATEGORY_ERROR
from plonemeeting.restapi.services.add import ANNEX_DECISION_RELATED_NOT_ITEM_ERROR
from plonemeeting.restapi.services.add import IGNORE_VALIDATION_FOR_REQUIRED_ERROR
from plonemeeting.restapi.services.add import IGNORE_VALIDATION_FOR_VALUED_ERROR
from plonemeeting.restapi.services.add import IGNORE_VALIDATION_FOR_WARNING
from plonemeeting.restapi.services.add import OPTIONAL_FIELD_ERROR
from plonemeeting.restapi.services.add import OPTIONAL_FIELDS_WARNING
from plonemeeting.restapi.services.add import ORG_FIELD_VALUE_ERROR
from plonemeeting.restapi.testing import PM_REST_TEST_ADD_ANNEXES_PROFILE_FUNCTIONAL
from plonemeeting.restapi.testing import PM_REST_TEST_ADD_PROFILE_FUNCTIONAL
from plonemeeting.restapi.tests.base import BaseTestCase
from plonemeeting.restapi.tests.config import base64_pdf_data
from plonemeeting.restapi.utils import IN_NAME_OF_USER_NOT_FOUND
from Products.CMFPlone.utils import safe_unicode
from Products.PloneMeeting.tests.PloneMeetingTestCase import DEFAULT_USER_PASSWORD
from Products.PloneMeeting.utils import get_annexes

import pytz
import transaction


class testServiceAdd(BaseTestCase):
    """@item/@meeting POST endpoints."""

    layer = PM_REST_TEST_ADD_PROFILE_FUNCTIONAL

    def tearDown(self):
        self.api_session.close()
        transaction.abort()

    def test_restapi_add_item_config_id_not_found(self):
        """The 'config_id' parameter must be given"""
        transaction.begin()
        endpoint_url = "{0}/@item".format(self.portal_url)
        response = self.api_session.post(endpoint_url, json={"config_id": "unknown"})
        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.json(),
            {u"message": CONFIG_ID_NOT_FOUND_ERROR % "unknown", u"type": u"Exception"},
        )

    def test_restapi_add_item_required_params(self):
        """A valid 'config_id' must be given"""
        self.changeUser("pmManager")
        pmFolder = self.getMeetingFolder()
        self.assertEqual(len(pmFolder.objectIds("MeetingItem")), 0)
        endpoint_url = "{0}/@item".format(self.portal_url)
        response = self.api_session.post(endpoint_url)
        transaction.commit()
        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.json(), {u"message": CONFIG_ID_ERROR, u"type": u"Exception"}
        )
        response = self.api_session.post(
            endpoint_url,
            json={
                "config_id": self.meetingConfig.getId(),
                "proposingGroup": self.developers_uid,
                "title": "My item",
            },
        )
        transaction.begin()
        self.assertEqual(response.status_code, 201, response.content)
        pmFolder = self.getMeetingFolder()
        self.assertEqual(len(pmFolder.objectIds("MeetingItem")), 1)
        item = pmFolder.get("my-item")
        self.assertEqual(item.Title(), "My item")
        self.assertEqual(item.getProposingGroup(), self.developers_uid)

    def test_restapi_add_item_ids_into_uids_error(self):
        """When creating an item, for convenience, fields holding organizations
           like "proposingGroup", "groupsInCharge", ... may have the organization id
           even if finally the UID is stored.
           If a wrong id/UID is given, an error is raised."""
        transaction.begin()
        endpoint_url = "{0}/@item".format(self.portal_url)
        response = self.api_session.post(
            endpoint_url,
            json={
                "config_id": self.meetingConfig.getId(),
                "proposingGroup": "wrong-id",
                "title": "My item",
            },
        )
        transaction.begin()
        self.assertEqual(response.status_code, 400, response.content)
        self.assertEqual(
            response.json(),
            {u"message": ORG_FIELD_VALUE_ERROR % ("wrong-id", "proposingGroup"),
             u"type": u"BadRequest"}
        )

    def test_restapi_add_item_optional_fields(self):
        """When creating an item, given optional fields must be enabled in config."""
        cfg = self.meetingConfig
        self.assertFalse("notes" in cfg.getUsedItemAttributes())
        self.changeUser("pmManager")
        endpoint_url = "{0}/@item".format(self.portal_url)
        json = {
            "config_id": cfg.getId(),
            "proposingGroup": self.developers_uid,
            "title": "My item",
            "notes": u"<p>My notes</p>",
        }
        response = self.api_session.post(endpoint_url, json=json)
        transaction.begin()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {u"message": OPTIONAL_FIELD_ERROR % "notes", u"type": u"BadRequest"}
        )
        self._enableField("notes")
        transaction.commit()
        response = self.api_session.post(endpoint_url, json=json)
        transaction.begin()
        self.assertEqual(response.status_code, 201, response.content)
        pmFolder = self.getMeetingFolder()
        item = pmFolder.objectValues()[-1]
        self.assertEqual(item.Title(), json["title"])
        self.assertEqual(item.getProposingGroup(), json["proposingGroup"])
        self.assertEqual(item.getNotes(), json["notes"])

    def test_restapi_add_item_optional_fields_ignore_not_used_data(self):
        """When creating an item, given optional fields must be enabled in config,
           but when using parameter "ignore_not_used_data=true" then a warning
           is added instead raising an error."""
        cfg = self.meetingConfig
        self.assertFalse("notes" in cfg.getUsedItemAttributes())
        self.changeUser("pmManager")
        endpoint_url = "{0}/@item".format(self.portal_url)
        json = {
            "config_id": cfg.getId(),
            "proposingGroup": self.developers_uid,
            "title": "My item",
            "notes": u"<p>My notes</p>",
            "ignore_not_used_data": True
        }
        response = self.api_session.post(endpoint_url, json=json)
        transaction.begin()
        self.assertEqual(response.status_code, 201, response.content)
        self.assertTrue(OPTIONAL_FIELDS_WARNING % "notes" in response.json()['@warnings'])
        pmFolder = self.getMeetingFolder()
        item = pmFolder.objectValues()[-1]
        self.assertEqual(item.Title(), json["title"])
        self.assertEqual(item.getProposingGroup(), json["proposingGroup"])
        # optional field not enable was ignore
        self.assertFalse(item.getNotes())

    def test_restapi_add_item_org_fields(self):
        """When creating an item, values for fields storing organization
           uids may receive organizations ids instead to ease use by externals."""
        cfg = self.meetingConfig
        cfg.setOrderedGroupsInCharge([self.vendors_uid])
        self._enableField("groupsInCharge")
        self._enableField("associatedGroups")
        self.changeUser("pmManager")
        transaction.commit()
        endpoint_url = "{0}/@item".format(self.portal_url)
        json = {
            "config_id": cfg.getId(),
            "proposingGroup": self.developers.getId(),
            "groupsInCharge": [self.vendors.getId(), self.developers.getId()],
            "associatedGroups": [self.vendors.getId(), self.developers.getId()],
            "optionalAdvisers": [self.vendors.getId()],
            "title": "My item",
        }
        response = self.api_session.post(endpoint_url, json=json)
        transaction.begin()
        self.assertEqual(response.status_code, 201, response.content)
        pmFolder = self.getMeetingFolder()
        item = pmFolder.objectValues()[-1]
        self.assertEqual(item.Title(), json["title"])
        # turned to UIDs
        self.assertEqual(item.getProposingGroup(), self.developers_uid)
        self.assertEqual(
            item.getGroupsInCharge(), [self.vendors_uid, self.developers_uid]
        )
        self.assertEqual(
            item.getAssociatedGroups(), (self.vendors_uid, self.developers_uid)
        )
        self.assertEqual(item.getOptionalAdvisers(), (self.vendors_uid,))
        self.assertTrue(self.vendors_uid in item.adviceIndex)

    def test_restapi_add_item_wf_transitions_present(self):
        """When creating an item, we may define "wf_transitions"
           until "present", in this case, item is "presented" in next meeting."""
        cfg = self.meetingConfig
        self.changeUser("pmManager")
        # meeting in the future
        date = DateTime() + 1
        if HAS_MEETING_DX:
            date = datetime.now() + timedelta(days=1)
        meeting = self.create("Meeting", date=date)
        endpoint_url = "{0}/@item".format(self.portal_url)
        json = {
            "config_id": cfg.getId(),
            "proposingGroup": self.developers.getId(),
            "title": "My item",
            "wf_transitions": ["propose", "validate", "present"]
        }
        transaction.commit()
        response = self.api_session.post(endpoint_url, json=json)
        transaction.begin()
        self.assertEqual(response.status_code, 201, response.content)
        pmFolder = self.getMeetingFolder()
        item = pmFolder.objectValues()[-1]
        self.assertEqual(self.get_review_state(item), "presented")
        self.assertEqual(item.getMeeting(), meeting)

    def test_restapi_add_item_in_name_of(self):
        """Test while using 'in_name_of' parameter"""
        cfg = self.meetingConfig
        # must be (Meeting)Manager to use in_name_of
        self.api_session.auth = ("pmCreator1", DEFAULT_USER_PASSWORD)
        endpoint_url = "{0}/@item".format(self.portal_url)
        json = {
            "config_id": cfg.getId(),
            "proposingGroup": self.vendors_uid,
            "title": "My item",
            "in_name_of": "pmCreator2",
        }
        response = self.api_session.post(endpoint_url, json=json)
        transaction.begin()
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
        json["in_name_of"] = "unknown"
        response = self.api_session.post(endpoint_url, json=json)
        transaction.begin()
        self.assertEqual(
            response.json(),
            {u"message": IN_NAME_OF_USER_NOT_FOUND % "unknown", u"type": u"BadRequest"},
        )
        # now as MeetingManager for pmCreator2
        json["in_name_of"] = "pmCreator2"
        response = self.api_session.post(endpoint_url, json=json)
        transaction.begin()
        self.assertEqual(response.status_code, 201, response.content)
        # item was created in the pmCreator2 folder
        response_json = response.json()
        self.assertEqual(response_json["creators"], [u"pmCreator2"])
        self.assertTrue("Members/pmCreator2/mymeetings" in response_json["@id"])

    def test_restapi_add_item_external_identifier(self):
        """When creating an item, we may receive an externalIdentifier",
           in this case it is stored on the created item."""
        cfg = self.meetingConfig
        self.changeUser("pmManager")
        endpoint_url = "{0}/@item".format(self.portal_url)
        json = {
            "config_id": cfg.getId(),
            "proposingGroup": self.developers.getId(),
            "title": "My item",
            # may sometimes be given as an integer
            "externalIdentifier": 123
        }
        response = self.api_session.post(endpoint_url, json=json)
        transaction.begin()
        self.assertEqual(response.status_code, 201, response.content)
        pmFolder = self.getMeetingFolder()
        item = pmFolder.objectValues()[-1]
        # is forced to str when stored
        self.assertEqual(item.externalIdentifier, "123")
        brains = self.catalog(externalIdentifier="123")
        self.assertEqual(len(brains), 1)
        self.assertEqual(brains[0].UID, item.UID())

    def test_restapi_add_item_ignore_validation_for(self):
        """When creating an item, it is possible to define
           a list of fields to bypass validation for if it is empty."""
        cfg = self.meetingConfig
        cfg.setUseGroupsAsCategories(False)
        self._enableField("classifier")
        transaction.commit()
        self.changeUser("pmManager")
        endpoint_url = "{0}/@item".format(self.portal_url)
        json = {
            "config_id": cfg.getId(),
            "proposingGroup": self.developers.getId(),
            "title": "My item",
            "category": "unknown",
            "classifier": "classifier1"
        }
        # when using categories, creating an item without category fails
        response = self.api_session.post(endpoint_url, json=json)
        self.assertEqual(response.status_code, 400, response.content)
        self.assertEqual(
            response.json(),
            {u'message': u"[{'field': 'category', 'message': u'Please select a category.', "
                         u"'error': 'ValidationError'}]",
             u'type': u'BadRequest'}
        )
        # when using "ignore_validation_for", some required fields
        # validation may not be bypassed
        json["title"] = ""
        json["ignore_validation_for"] = ["title"]
        response = self.api_session.post(endpoint_url, json=json)
        self.assertEqual(response.status_code, 400, response.content)
        self.assertEqual(
            response.json(),
            {
                u"message":
                    IGNORE_VALIDATION_FOR_REQUIRED_ERROR % "title, proposingGroup",
                u"type": u"BadRequest",
            }
        )
        # when using "ignore_validation_for", only empty values
        # (or not given at all) validation may be bypassed
        json["title"] = "My item"
        json["ignore_validation_for"] = ["category"]
        response = self.api_session.post(endpoint_url, json=json)
        self.assertEqual(response.status_code, 400, response.content)
        self.assertEqual(
            response.json(),
            {
                u"message": IGNORE_VALIDATION_FOR_VALUED_ERROR % "category",
                u"type": u"BadRequest",
            }
        )
        # use "ignore_validation_for" correctly
        # bypass category validation and classifier validation
        # remove category from data and pass an empty classifier
        # check also that such an item may be set to WF state "validated"
        json["ignore_validation_for"] = ["category", "classifier"]
        json.pop("category")
        json["classifier"] = None
        # triggering transitions without category only works with PM4.2+
        if HAS_MEETING_DX:
            json["wf_transitions"] = ["propose", "validate"]
        response = self.api_session.post(endpoint_url, json=json)
        transaction.begin()
        self.assertEqual(response.status_code, 201, response.content)
        pmFolder = self.getMeetingFolder()
        item = pmFolder.objectValues()[-1]
        self.assertEqual(item.getCategory(), "")
        self.assertEqual(item.getClassifier(), "")
        # a warning was added nevertheless
        self.assertEqual(response.json()['@warnings'],
                         [IGNORE_VALIDATION_FOR_WARNING % "category, classifier"])
        # use getInfoFor instead query_state for PM 4.1/4.2 compat
        if HAS_MEETING_DX:
            self.assertEqual(self.get_review_state(item), "validated")

    def test_restapi_add_item_wf_transitions(self):
        """When creating an item, we may define "wf_transitions"."""
        cfg = self.meetingConfig
        self.changeUser("pmManager")
        endpoint_url = "{0}/@item".format(self.portal_url)
        json = {
            "config_id": cfg.getId(),
            "proposingGroup": self.developers.getId(),
            "title": "My item",
            "wf_transitions": ["propose", "validate"]
        }
        response = self.api_session.post(endpoint_url, json=json)
        transaction.begin()
        self.assertEqual(response.status_code, 201, response.content)
        pmFolder = self.getMeetingFolder()
        item = pmFolder.objectValues()[-1]
        self.assertEqual(self.get_review_state(item), "validated")

    def test_restapi_add_annex_to_existing_element(self):
        """Use the @annex POST endpoint to create an annex."""
        cfg = self.meetingConfig
        self._removeConfigObjectsFor(cfg)
        self.changeUser("pmManager")
        item = self.create('MeetingItem')
        item_uid = item.UID()
        date = None
        if not HAS_MEETING_DX:
            date = DateTime()
        meeting = self.create('Meeting', date=date)
        meeting_uid = meeting.UID()
        transaction.commit()

        # add annex to item
        json = {
            "title": "My annex",
            "content_category": "wrong-annex",
            "file": {
                "data": "123456",
                "encoding": "ascii",
                "filename": "file.txt"}
            }
        endpoint_url = "{0}/@annex/{1}".format(self.portal_url, item_uid)
        # wrong content_category
        response = self.api_session.post(endpoint_url, json=json)
        self.assertEqual(response.status_code, 400, response.content)
        self.assertEqual(
            response.json(),
            {u"message": ANNEX_CONTENT_CATEGORY_ERROR % "wrong-annex",
             u"type": u"BadRequest"}
        )
        # add annex to item correctly
        json["content_category"] = "item-annex"
        response = self.api_session.post(endpoint_url, json=json)
        transaction.begin()
        self.assertEqual(response.status_code, 201, response.content)
        # adding an annex without "content_category" will use default one
        # the default annex type is "financial-analysis"
        json.pop("content_category")
        response = self.api_session.post(endpoint_url, json=json)
        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(response.json()["content_category"]["title"], u'Financial analysis')
        # add annexDecision to item correctly
        json["content_category"] = "decision-annex"
        json["decision_related"] = True
        response = self.api_session.post(endpoint_url, json=json)
        self.assertEqual(response.status_code, 201, response.content)
        # add annex to meeting
        # can not use parameter "decision_related" on a meeting
        json["content_category"] = "meeting-annex"
        endpoint_url = endpoint_url.replace(item_uid, meeting_uid)
        response = self.api_session.post(endpoint_url, json=json)
        self.assertEqual(response.status_code, 400, response.content)
        self.assertEqual(
            response.json(),
            {u"message": ANNEX_DECISION_RELATED_NOT_ITEM_ERROR,
             u"type": u"BadRequest"}
        )
        # add annex to meeting correctly
        json["decision_related"] = False
        response = self.api_session.post(endpoint_url, json=json)
        self.assertEqual(response.status_code, 201, response.content)
        transaction.begin()

        # annexes were added to item and meeting
        item_annexes = get_annexes(item, ["annex"])
        self.assertEqual(len(item_annexes), 2)
        decision_annexes = get_annexes(item, ["annexDecision"])
        self.assertEqual(len(decision_annexes), 1)
        meeting_annexes = get_annexes(meeting)
        self.assertEqual(len(meeting_annexes), 1)

    def test_restapi_add_item_clean_html(self):
        """When creating an item, HTML will be cleaned by default.
           Adding 'clean_html':false in the body will disable it."""
        cfg = self.meetingConfig
        self.changeUser("pmManager")
        endpoint_url = "{0}/@item".format(self.portal_url)
        dirty_html = '<span class="ms-class">Hello, &#xa0; la d\xc3\xa9cision ' \
            '\xc3\xa9tait longue!</span><br /><strong>'
        json = {
            "config_id": cfg.getId(),
            "proposingGroup": self.developers.getId(),
            "title": "My item",
            # some dirty HTML
            "decision": dirty_html,
        }
        response = self.api_session.post(endpoint_url, json=json)
        transaction.begin()
        self.assertEqual(response.status_code, 201, response.content)
        pmFolder = self.getMeetingFolder()
        item1 = pmFolder.objectValues()[-1]
        # decision was cleaned
        self.assertEqual(
            item1.getDecision(),
            '<p><span class="ms-class">Hello, \xc2\xa0 la d\xc3\xa9cision '
            '\xc3\xa9tait longue!</span><br /><strong></strong></p>')
        # create item with clean_html=False
        json['clean_html'] = False
        response = self.api_session.post(endpoint_url, json=json)
        transaction.begin()
        self.assertEqual(response.status_code, 201, response.content)
        # decision was not cleaned
        item2 = pmFolder.objectValues()[-1]
        self.assertEqual(item2.getDecision(), dirty_html)

    def test_restapi_add_clean_meeting(self):
        """When creating an meeting, HTML will be cleaned by default."""
        transaction.begin()
        self._enableField("observations", related_to="Meeting")
        # make sure creating a meeting work when using attendees
        self._enableField("attendees", related_to="Meeting")
        transaction.commit()
        cfg = self.meetingConfig
        self.changeUser("pmManager")
        endpoint_url = "{0}/@meeting".format(self.portal_url)
        dirty_html = '<span class="ms-class">&#xa0; hello h\xc3\xa9h\xc3\xa9'
        date = datetime.now(tz=pytz.UTC).isoformat().replace("+00:00", "Z")
        json = {
            "config_id": cfg.getId(),
            "date": date,
            # some dirty HTML
            "observations": dirty_html,
        }
        response = self.api_session.post(endpoint_url, json=json)
        transaction.begin()
        self.assertEqual(response.status_code, 201, response.content)
        pmFolder = self.getMeetingFolder()
        meeting = object_values(pmFolder, "Meeting")[-1]
        # dirty_html was cleaned
        self.assertEqual(
            meeting.observations.raw,
            u'<p><span class="ms-class">\xa0 hello h\xe9h\xe9</span></p>')
        # this fails with AT Meeting because mimetype is considered text/plain
        if HAS_MEETING_DX:
            # create meeting with clean_html=False
            json['clean_html'] = False
            # change date, can not create several meeting with same date
            date = date[0:3] + str(int(date[3]) + 1) + date[4:]
            json['date'] = date
            response = self.api_session.post(endpoint_url, json=json)
            transaction.begin()
            self.assertEqual(response.status_code, 201, response.content)
            pmFolder = self.getMeetingFolder()
            meeting2 = object_values(pmFolder, "Meeting")[-1]
            # the "&#xa0;" is replaced by "\xa0" by Plone but could also
            # be removed while using appy.pod pre processor
            meeting_dirty_html = safe_unicode(dirty_html).replace(u'&#xa0;', u'\xa0')
            self.assertEqual(meeting2.observations.raw, meeting_dirty_html)
            # trying to add meeting with same date will fail
            response = self.api_session.post(endpoint_url, json=json)
            self.assertEqual(response.status_code, 400, response.content)
            self.assertEqual(
                response.json(),
                {u'message': u"[{'message': 'A meeting having the same date and hour "
                    u"already exists. Please choose another date and/or hour.', "
                    u"'error': 'ValidationError'}]",
                 u'type': u'BadRequest'})


class testServiceAddWithAnnexes(BaseTestCase):
    """@item/@meeting POST endpoints with annexes."""

    layer = PM_REST_TEST_ADD_ANNEXES_PROFILE_FUNCTIONAL

    def tearDown(self):
        self.api_session.close()
        transaction.abort()

    def test_restapi_add_item_with_annexes(self):
        """When creating an item, we may add annexes as __children__."""
        cfg = self.meetingConfig
        self.changeUser("pmManager")
        endpoint_url = "{0}/@item".format(self.portal_url)
        json = {
            "config_id": cfg.getId(),
            "proposingGroup": self.developers.getId(),
            "title": "My item",
            "__children__": [
                {
                    "@type": "annex",
                    "title": "My annex",
                    "content_category": "item-annex",
                    "file": {
                        "data": "123456",
                        "encoding": "ascii",
                        "filename": "file.txt",
                    },
                },
            ],
        }
        response = self.api_session.post(endpoint_url, json=json)
        transaction.begin()
        self.assertEqual(response.status_code, 201, response.content)
        pmFolder = self.getMeetingFolder()
        item = pmFolder.objectValues()[-1]
        self.assertEqual(item.Title(), json["title"])
        annex = get_annexes(item)[0]
        self.assertEqual(annex.title, json["__children__"][0]["title"])
        self.assertEqual(
            annex.content_category,
            calculate_category_id(cfg.annexes_types.item_annexes.get("item-annex")),
        )
        self.assertEqual(
            annex.file.filename, json["__children__"][0]["file"]["filename"]
        )
        self.assertEqual(annex.file.size, 6)
        self.assertEqual(annex.file.contentType, "text/plain")

    def test_restapi_add_item_with_annexes_and_check_encoding(self):
        """When creating an item, we may add annexes as __children__,
           if encoding not given, we assume it is 'base64'."""
        cfg = self.meetingConfig
        self.changeUser("pmManager")
        endpoint_url = "{0}/@item".format(self.portal_url)
        json = {
            "config_id": cfg.getId(),
            "proposingGroup": self.developers.getId(),
            "title": "My item",
            "__children__": [
                {
                    "@type": "annex",
                    "title": "My annex",
                    "content_category": "item-annex",
                    "file": {"data": base64_pdf_data, "filename": "file.pdf"},
                },
            ],
        }
        response = self.api_session.post(endpoint_url, json=json)
        transaction.begin()
        self.assertEqual(response.status_code, 201, response.content)
        pmFolder = self.getMeetingFolder()
        item = pmFolder.objectValues()[-1]
        annex = get_annexes(item)[0]
        self.assertEqual(
            annex.file.filename, json["__children__"][0]["file"]["filename"]
        )
        self.assertEqual(annex.file.size, 6475)
        self.assertEqual(annex.file.contentType, "application/pdf")

    def test_restapi_add_item_with_annexes_and_content_category(self):
        """When creating an item, we may add annexes as __children__,
           if using wrong content_category, cration is aborted."""
        cfg = self.meetingConfig
        self.changeUser("pmManager")
        endpoint_url = "{0}/@item".format(self.portal_url)
        json = {
            "config_id": cfg.getId(),
            "proposingGroup": self.developers.getId(),
            "title": "My item",
            "__children__": [
                {
                    "@type": "annex",
                    "title": "My annex",
                    "content_category": "unknown",
                    "file": {
                        "data": "123456",
                        "encoding": "ascii",
                        "filename": "file.txt",
                    },
                },
            ],
        }
        response = self.api_session.post(endpoint_url, json=json)
        transaction.begin()
        self.assertEqual(response.status_code, 400, response.content)
        self.assertEqual(
            response.json(),
            {
                u"message": ANNEX_CONTENT_CATEGORY_ERROR % "unknown",
                u"type": u"BadRequest",
            }
        )

    def test_restapi_add_item_with_annexes_and_filename_or_content_type_required(self):
        """When creating an item, we may add annexes as __children__,
           one of 'filename' or 'content-type' is required to determinate content_type."""
        transaction.begin()
        cfg = self.meetingConfig
        self.changeUser("pmManager")
        endpoint_url = "{0}/@item".format(self.portal_url)
        json = {
            "config_id": cfg.getId(),
            "proposingGroup": self.developers.getId(),
            "title": "My item",
            "__children__": [
                {
                    "@type": "annex",
                    "title": "My annex",
                    "content_category": "unknown",
                    "file": {
                        "data": "123456",
                        "encoding": "ascii",
                        "filename": "file.txt",
                    },
                },
            ],
        }
        response = self.api_session.post(endpoint_url, json=json)
        transaction.begin()
        self.assertEqual(response.status_code, 400, response.content)
        self.assertEqual(
            response.json(),
            {
                u"message": ANNEX_CONTENT_CATEGORY_ERROR % "unknown",
                u"type": u"BadRequest",
            }
        )

    def test_restapi_add_item_with_annexes_children(self):
        """When creating an item, we may add annexes as __children__,
           we may add several annexes at once."""
        cfg = self.meetingConfig
        self.changeUser("pmManager")
        endpoint_url = "{0}/@item".format(self.portal_url)
        json = {
            "config_id": cfg.getId(),
            "proposingGroup": self.developers.getId(),
            "title": "My item",
            "__children__": [
                {
                    "@type": "annex",
                    "title": "My annex 1",
                    "content_category": "item-annex",
                    "file": {
                        "data": "123456",
                        "encoding": "ascii",
                        "filename": "file.txt",
                    },
                },
                {
                    "@type": "annex",
                    "title": "My annex 2",
                    "content_category": "item-annex",
                    "file": {"data": base64_pdf_data, "filename": "file.pdf"},
                },
            ],
        }
        response = self.api_session.post(endpoint_url, json=json)
        transaction.commit()
        # this tries to manage randomly failing test
        try:
            self.assertEqual(response.status_code, 201, response.content)
        except Exception:
            response = self.api_session.post(endpoint_url, json=json)
            transaction.commit()
            self.assertEqual(response.status_code, 201, response.content)
        pmFolder = self.getMeetingFolder()
        item = pmFolder.objectValues()[-1]
        annex1 = get_annexes(item)[0]
        annex2 = get_annexes(item)[1]
        self.assertEqual(
            annex1.file.filename, json["__children__"][0]["file"]["filename"]
        )
        self.assertEqual(annex1.file.size, 6)
        self.assertEqual(annex1.file.contentType, "text/plain")
        self.assertEqual(
            annex2.file.filename, json["__children__"][1]["file"]["filename"]
        )
        self.assertEqual(annex2.file.size, 6475)
        self.assertEqual(annex2.file.contentType, "application/pdf")

    def test_restapi_add_a_meeting_with_annexes(self):
        """When creating a meeting, we may add annexes as __children__,
           we may add several annexes at once."""
        cfg = self.meetingConfig
        self.changeUser("pmManager")
        endpoint_url = "{0}/@item".format(self.portal_url)
        json = {
            "config_id": cfg.getId(),
            "date": "2022-02-02 12:00",
            "__children__": [
                {
                    "@type": "annex",
                    "title": "My annex 1",
                    "file": {
                        "data": "123456",
                        "encoding": "ascii",
                        "filename": "file.txt",
                    },
                },
                {
                    "@type": "annex",
                    "title": "My annex 2",
                    "file": {"data": base64_pdf_data, "filename": "file.pdf"},
                },
            ],
        }
        response = self.api_session.post(endpoint_url, json=json)
        transaction.begin()
        self.assertEqual(response.status_code, 201, response.content)
        pmFolder = self.getMeetingFolder()
        meeting = pmFolder.objectValues()[-1]
        annex1 = get_annexes(meeting)[0]
        annex2 = get_annexes(meeting)[1]
        self.assertEqual(
            annex1.file.filename, json["__children__"][0]["file"]["filename"]
        )
        self.assertEqual(annex1.file.size, 6)
        self.assertEqual(annex1.file.contentType, "text/plain")
        self.assertEqual(
            annex2.file.filename, json["__children__"][1]["file"]["filename"]
        )
        self.assertEqual(annex2.file.size, 6475)
        self.assertEqual(annex2.file.contentType, "application/pdf")


def test_suite():
    from unittest import TestSuite, makeSuite

    suite = TestSuite()
    # add a prefix to avoid every PM tests to be executed
    suite.addTest(makeSuite(testServiceAdd, prefix="test_restapi_"))
    suite.addTest(makeSuite(testServiceAddWithAnnexes, prefix="test_restapi_"))
    return suite
