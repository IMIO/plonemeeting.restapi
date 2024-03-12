# -*- coding: utf-8 -*-

from os import path
from plone.restapi.testing import RelativeSession
from plonemeeting.restapi.testing import PM_REST_TEST_PROFILE_FUNCTIONAL
from Products.PloneMeeting import tests as pm_tests
from Products.PloneMeeting.tests.PloneMeetingTestCase import DEFAULT_USER_PASSWORD
from Products.PloneMeeting.tests.PloneMeetingTestCase import PloneMeetingTestCase

import os
import transaction


class BaseTestCase(PloneMeetingTestCase):
    """Base class for defining PM restapi test cases."""

    layer = PM_REST_TEST_PROFILE_FUNCTIONAL

    def setUp(self):
        """ """
        super(BaseTestCase, self).setUp()
        self.portal_url = self.portal.absolute_url()

        self.api_session = RelativeSession(self.portal_url)
        self.api_session.headers.update({"Accept": "application/json"})
        self.api_session.auth = ("pmManager", DEFAULT_USER_PASSWORD)
        self.changeUser("siteadmin")
        # avoid sometimes failing test on jenkins...
        try:
            self.getMeetingFolder(userId="pmManager")
        except:
            transaction.commit()
            self.getMeetingFolder(userId="pmManager")

        # enable RESTAPI_DEBUG for every tests
        # this will display the result of a restapi call in the log
        os.environ['RESTAPI_DEBUG'] = "True"
        try:
            transaction.commit()
        except Exception:
            transaction.begin()

    def _add_image(self, obj):
        """ """
        file_path = path.join(path.dirname(pm_tests.__file__), "dot.gif")
        data = open(file_path, "r")
        img_id = obj.invokeFactory("Image", id="dot.gif", title="Image", file=data.read())
        img = getattr(obj, img_id)
        return img
