# -*- coding: utf-8 -*-

from plone.restapi.deserializer import json_body
from plone.restapi.deserializer.atfields import DefaultFieldDeserializer
from plone.restapi.interfaces import IFieldDeserializer
from plonemeeting.restapi.utils import clean_html
from Products.Archetypes.interfaces import IBaseObject
from Products.Archetypes.interfaces.field import ITextField
from zope.component import adapter
from zope.interface import implementer
from zope.publisher.interfaces.browser import IBrowserRequest


@implementer(IFieldDeserializer)
@adapter(ITextField, IBaseObject, IBrowserRequest)
class TextFieldDeserializer(DefaultFieldDeserializer):
    def __call__(self, value):
        kwargs = {}
        should_clean_html = json_body(self.request).get('clean_html', True)
        if should_clean_html and value:
            value, warn_wrong_html = clean_html(value)
            kwargs['warn_wrong_html'] = warn_wrong_html
        return value, kwargs
