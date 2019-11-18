# -*- coding: utf-8 -*-

from plone.restapi.interfaces import ISerializeToJson
from plonemeeting.restapi.serializer.base import BaseSerializeToJson
from Products.PloneMeeting.interfaces import IMeetingItem
from zope.component import adapter
from zope.interface import implementer
from zope.interface import Interface


@implementer(ISerializeToJson)
@adapter(IMeetingItem, Interface)
class SerializeToJson(BaseSerializeToJson):
    ''' '''
