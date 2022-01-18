# -*- coding: utf-8 -*-

from plone.app.textfield.interfaces import IRichText
from plone.dexterity.interfaces import IDexterityContent
from plone.restapi.deserializer.dxfields import RichTextFieldDeserializer
from plone.restapi.interfaces import IFieldDeserializer
from plonemeeting.restapi.interfaces import IPMRestapiLayer
from plonemeeting.restapi.utils import clean_html
from zope.component import adapter
from zope.interface import implementer


@implementer(IFieldDeserializer)
@adapter(IRichText, IDexterityContent, IPMRestapiLayer)
class PMRichTextFieldDeserializer(RichTextFieldDeserializer):
    def __call__(self, value):

        value = super(PMRichTextFieldDeserializer, self).__call__(value)
        value._raw_holder.value = clean_html(value.raw)
        return value
