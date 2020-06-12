# -*- coding: utf-8 -*-

from plone.app.testing import FunctionalTesting
from plone.restapi.testing import PLONE_RESTAPI_AT_FUNCTIONAL_TESTING
from Products.PloneMeeting.testing import PMLayer

import plonemeeting.restapi


class PMRestapiLayer(PMLayer):
    ''' '''


PM_REST_TESTING_PROFILE = PMRestapiLayer(
    zcml_filename="testing.zcml",
    zcml_package=plonemeeting.restapi,
    additional_z2_products=('imio.dashboard',
                            'Products.PloneMeeting',
                            'Products.CMFPlacefulWorkflow',
                            'Products.PasswordStrength'),
    gs_profile_id='plonemeeting.restapi:testing',
    name="PM_REST_TESTING_PROFILE")


PM_REST_TEST_PROFILE_FUNCTIONAL = FunctionalTesting(
    bases=(PM_REST_TESTING_PROFILE,
           PLONE_RESTAPI_AT_FUNCTIONAL_TESTING),
    name="PM_REST_TEST_PROFILE_FUNCTIONAL")


PM_REST_TEST_ADD_PROFILE_FUNCTIONAL = FunctionalTesting(
    bases=(PM_REST_TESTING_PROFILE,
           PLONE_RESTAPI_AT_FUNCTIONAL_TESTING),
    name="PM_REST_TEST_ADD_PROFILE_FUNCTIONAL")
