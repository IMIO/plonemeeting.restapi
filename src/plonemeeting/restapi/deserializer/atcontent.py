# -*- coding: utf-8 -*-

from plone import api
from plone.restapi.deserializer import json_body
from plone.restapi.deserializer.atcontent import DeserializeFromJson as ATDeserializeFromJson
from plone.restapi.interfaces import IDeserializeFromJson
from plone.restapi.interfaces import IFieldDeserializer
from Products.Archetypes.event import ObjectEditedEvent
from Products.Archetypes.event import ObjectInitializedEvent
from Products.PloneMeeting.interfaces import IATMeetingContent
from zExceptions import BadRequest
from zope.component import adapter
from zope.component import queryMultiAdapter
from zope.event import notify
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
            wfTool = api.portal.get_tool("portal_workflow")
            wf = wfTool.getWorkflowsFor(self.context)[0]
            wf.updateRoleMappingsFor(self.context)

        # XXX overrided until https://github.com/plone/plone.restapi/pull/1387 is merged
        #return super(DeserializeFromJson, self).__call__(
        #    validate_all=validate_all, data=data, create=create
        #)

        if data is None:
            data = json_body(self.request)

        obj = self.context
        modified = False

        for field in obj.Schema().fields():
            if not field.writeable(obj):
                continue

            name = field.getName()

            if name in data:
                deserializer = queryMultiAdapter(
                    (field, obj, self.request), IFieldDeserializer
                )
                if deserializer is None:
                    continue
                value, kwargs = deserializer(data[name])
                mutator = field.getMutator(obj)
                mutator(value, **kwargs)
                modified = True

        if create or modified:
            errors = self.validate()
            if not validate_all:
                errors = {f: e for f, e in errors.items() if f in data}
            if errors:
                errors = [
                    {"message": e, "field": f, "error": "ValidationError"}
                    for f, e in errors.items()
                ]
                raise BadRequest(errors)

            if create:
                if obj.checkCreationFlag():
                    obj.unmarkCreationFlag()
                notify(ObjectInitializedEvent(obj))
                obj.at_post_create_script()
            else:
                obj.reindexObject()
                notify(ObjectEditedEvent(obj))
                obj.at_post_edit_script()

        # We'll set the layout after the validation and and even if there
        # are no other changes.
        if "layout" in data:
            layout = data["layout"]
            self.context.setLayout(layout)

        # OrderingMixin
        self.handle_ordering(data)

        return obj

    def validate(self):
        """Handle "ignore_validation_for" that will specifically
           let ignore validation errors for given fields."""
        errors = super(DeserializeFromJson, self).validate()
        data = json_body(self.request)
        ignore_validation_for = data.get("ignore_validation_for", [])
        for field_name in ignore_validation_for:
            errors.pop(field_name, None)
        return errors
