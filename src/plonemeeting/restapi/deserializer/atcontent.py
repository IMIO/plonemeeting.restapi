# -*- coding: utf-8 -*-

from plone import api
from plone.restapi.deserializer.atcontent import DeserializeFromJson as ATDeserializeFromJson
from plone.restapi.interfaces import IDeserializeFromJson
from Products.PloneMeeting.interfaces import IATMeetingContent
from zope.component import adapter
from zope.interface import implementer
from zope.interface import Interface


@implementer(IDeserializeFromJson)
@adapter(IATMeetingContent, Interface)
class DeserializeFromJson(ATDeserializeFromJson):
    """JSON deserializer for Archetypes content types
    """

    notifies_create = True

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self, validate_all=False, data=None, create=False):

        if create:
            wfTool = api.portal.get_tool('portal_workflow')
            wf = wfTool.getWorkflowsFor(self.context)[0]
            wf.updateRoleMappingsFor(self.context)
        return super(DeserializeFromJson, self).__call__(
            validate_all=validate_all, data=data, create=create)
