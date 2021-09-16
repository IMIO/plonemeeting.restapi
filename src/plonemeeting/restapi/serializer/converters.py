# -*- coding: utf-8 -*-

from plone.app.textfield.interfaces import IRichTextValue
from plone.dexterity.interfaces import IDexterityContent
from plone.restapi.interfaces import IContextawareJsonCompatible
from plone.restapi.serializer.converters import RichtextDXContextConverter
from Products.PloneMeeting.utils import convert2xhtml
from zope.component import adapter
from zope.interface import implementer


@adapter(IRichTextValue, IDexterityContent)
@implementer(IContextawareJsonCompatible)
class PMRichtextDXContextConverter(RichtextDXContextConverter):

    def __call__(self):
        result = super(PMRichtextDXContextConverter, self).__call__()
        result["data"] = convert2xhtml(self.context,
                                       result["data"],
                                       image_src_to_data=True,
                                       use_appy_pod_preprocessor=True)
        return result
