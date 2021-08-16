# -*- coding: utf-8 -*-

from imio.helpers.xhtml import imagesToData
from plone.app.textfield.interfaces import IRichTextValue
from plone.dexterity.interfaces import IDexterityContent
from plone.restapi.interfaces import IContextawareJsonCompatible
from plone.restapi.serializer.converters import RichtextDXContextConverter
from zope.component import adapter
from zope.interface import implementer


@adapter(IRichTextValue, IDexterityContent)
@implementer(IContextawareJsonCompatible)
class PMRichtextDXContextConverter(RichtextDXContextConverter):

    def __call__(self):
        result = super(PMRichtextDXContextConverter, self).__call__()
        result["data"] = imagesToData(self.context, result["data"])
        return result
