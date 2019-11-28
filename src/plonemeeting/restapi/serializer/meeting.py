# -*- coding: utf-8 -*-

from plone.restapi.interfaces import ISerializeToJson
from plonemeeting.restapi.serializer.base import BaseATSerializeToJson
from Products.PloneMeeting.interfaces import IMeeting
from zope.component import adapter
from zope.interface import implementer
from zope.interface import Interface


@implementer(ISerializeToJson)
@adapter(IMeeting, Interface)
class SerializeToJson(BaseATSerializeToJson):
    ''' '''
