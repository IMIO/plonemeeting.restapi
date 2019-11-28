# -*- coding: utf-8 -*-

from plone.restapi.interfaces import ISerializeToJson
from plone.restapi.serializer.atcontent import SerializeFolderToJson as ATSerializeFolderToJson
from plone.restapi.serializer.dxcontent import SerializeFolderToJson as DXSerializeFolderToJson
from Products.PloneMeeting.interfaces import IMeetingContent
from zope.component import adapter
from zope.interface import implementer
from zope.interface import Interface


@implementer(ISerializeToJson)
@adapter(IMeetingContent, Interface)
class BaseATSerializeToJson(ATSerializeFolderToJson):
    """ """


@implementer(ISerializeToJson)
@adapter(Interface, Interface)
class BaseDXSerializeToJson(DXSerializeFolderToJson):
    """ """
