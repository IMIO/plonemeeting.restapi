# -*- coding: utf-8 -*-

from plone.restapi.interfaces import IFieldSerializer
from plone.restapi.interfaces import ISerializeToJson
from plone.restapi.serializer.atcontent import SerializeFolderToJson
from Products.PloneMeeting.interfaces import IMeetingContent
from zope.component import adapter
from zope.component import queryMultiAdapter
from zope.interface import implementer
from zope.interface import Interface


@implementer(ISerializeToJson)
@adapter(IMeetingContent, Interface)
class BaseSerializeToJson(SerializeFolderToJson):

    def _serialized_data(self):
        ''' '''
        result = {
            # '@context': 'http://www.w3.org/ns/hydra/context.jsonld',
            "@id": self.context.absolute_url(),
            "id": self.context.id,
            "@type": self.context.portal_type,
            "review_state": self._get_workflow_state(self.context),
            "UID": self.context.UID(),
            "layout": self.context.getLayout(),
            "is_folderish": False,
        }

        for field in self.context.Schema().fields():
            if "r" not in field.mode or \
               not field.checkPermission("r", self.context):
                continue

            name = field.getName()
            serializer = queryMultiAdapter(
                (field, self.context, self.request), IFieldSerializer
            )
            if serializer is not None:
                result[name] = serializer()

        return result

    def __call__(self, version=None, include_items=False):
        result = self._serialized_data()
        return result
