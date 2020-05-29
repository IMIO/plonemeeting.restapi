# -*- coding: utf-8 -*-

from plone.restapi.interfaces import IPloneRestapiLayer
from zope.publisher.interfaces.browser import IDefaultBrowserLayer


class IPMRestapiLayer(IPloneRestapiLayer):
    """Marker interface that defines a browser layer."""
