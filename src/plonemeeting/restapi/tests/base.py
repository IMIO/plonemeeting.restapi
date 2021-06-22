# -*- coding: utf-8 -*-

from plone.restapi.testing import RelativeSession
from plonemeeting.restapi.serializer.meeting import HAS_MEETING_DX
from plonemeeting.restapi.testing import PM_REST_TEST_PROFILE_FUNCTIONAL
from Products.PloneMeeting.tests.PloneMeetingTestCase import DEFAULT_USER_PASSWORD
from Products.PloneMeeting.tests.PloneMeetingTestCase import PloneMeetingTestCase

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
        self.getMeetingFolder(userId="pmManager")
        transaction.commit()

    def get_review_state(self, obj):
        """Backward compat method that manage queryState/query_state."""
        if HAS_MEETING_DX:
            return obj.query_state()
        else:
            return obj.queryState()
