# -*- coding: utf-8 -*-

from plone.restapi.interfaces import IFieldSerializer
from plone.restapi.serializer.atfields import DefaultFieldSerializer
from plone.restapi.serializer.atfields import TextFieldSerializer
from plone.restapi.serializer.converters import json_compatible
from plonemeeting.restapi.interfaces import IPMRestapiLayer
from Products.Archetypes.interfaces import IBaseObject
from Products.Archetypes.interfaces.field import ILinesField
from Products.Archetypes.interfaces.field import IStringField
from Products.Archetypes.interfaces.field import ITextField
from Products.CMFCore.utils import getToolByName
from Products.PloneMeeting.utils import convert2xhtml
from zope.component import adapter
from zope.interface import implementer
from zope.interface import Interface


@adapter(IStringField, IBaseObject, Interface)
@implementer(IFieldSerializer)
class StringFieldSerializer(DefaultFieldSerializer):
    """Manage vocabulary for StringField."""
    def __call__(self):
        value = super(StringFieldSerializer, self).__call__()
        if self.field.vocabulary or self.field.vocabulary_factory:
            vocab = self.field.Vocabulary(self.context)
            value = {"token": value, "title": vocab.getValue(value)}
        return json_compatible(value)


@adapter(ILinesField, IBaseObject, Interface)
@implementer(IFieldSerializer)
class LinesFieldSerializer(DefaultFieldSerializer):
    """Manage vocabulary for LinesField."""
    def __call__(self):
        values = super(LinesFieldSerializer, self).__call__()
        if self.field.vocabulary or self.field.vocabulary_factory:
            result = []
            vocab = self.field.Vocabulary(self.context)
            for value in values:
                result.append({"token": value, "title": vocab.getValue(value)})
            values = result
        return json_compatible(values)


@adapter(ITextField, IBaseObject, IPMRestapiLayer)
@implementer(IFieldSerializer)
class PMTextFieldSerializer(TextFieldSerializer):
    """Manage images to data:image base64 values for text/html data."""
    def __call__(self):
        mimetypes_registry = getToolByName(self.context, "mimetypes_registry")
        data = super(TextFieldSerializer, self).__call__()
        content_type = json_compatible(mimetypes_registry(data)[2].normalized())
        if content_type == u'text/html':
            data = convert2xhtml(self.context,
                                 data,
                                 image_src_to_data=True,
                                 use_appy_pod_preprocessor=True)
        return {
            "content-type": json_compatible(content_type),
            "data": data,
        }
