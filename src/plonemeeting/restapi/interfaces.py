# -*- coding: utf-8 -*-

from imio.restapi.interfaces import IImioRestapiLayer
from plone.restapi.interfaces import IPloneRestapiLayer


class IPMRestapiLayer(IImioRestapiLayer, IPloneRestapiLayer):
    """Marker interface that defines a browser layer."""
