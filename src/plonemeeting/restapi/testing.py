# -*- coding: utf-8 -*-

from plone.app.robotframework.testing import REMOTE_LIBRARY_BUNDLE_FIXTURE
from plone.app.testing import applyProfile
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import PloneSandboxLayer
from plone.restapi.testing import PLONE_RESTAPI_AT_FUNCTIONAL_TESTING
from plone.testing import z2

import plonemeeting.restapi


class PMRestapiLayer(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # Load any other ZCML that is required for your tests.
        # The z3c.autoinclude feature is disabled in the Plone fixture base
        # layer.
        import plone.app.dexterity
        self.loadZCML(package=plone.app.dexterity)
        self.loadZCML(package=plonemeeting.restapi)

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'plonemeeting.restapi:default')


PM_RESTAPI_FIXTURE = PMRestapiLayer()


PM_RESTAPI_INTEGRATION_TESTING = IntegrationTesting(
    bases=(PM_RESTAPI_FIXTURE,),
    name='PMRestapiLayer:IntegrationTesting',
)


PM_RESTAPI_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(PM_RESTAPI_FIXTURE, PLONE_RESTAPI_AT_FUNCTIONAL_TESTING),
    name='PMRestapiLayer:FunctionalTesting',
)


PM_RESTAPI_ACCEPTANCE_TESTING = FunctionalTesting(
    bases=(
        PM_RESTAPI_FIXTURE,
        REMOTE_LIBRARY_BUNDLE_FIXTURE,
        z2.ZSERVER_FIXTURE,
    ),
    name='PMRestapiLayer:AcceptanceTesting',
)
