# -*- coding: utf-8 -*-

from plone.restapi.deserializer import boolean_value
from plone.restapi.interfaces import IExpandableElement
from plone.restapi.services import Service
from plonemeeting.restapi.config import ANNEXES_FILTER_VALUES
from plonemeeting.restapi.serializer.base import serialize_annexes
from Products.PloneMeeting.interfaces import IMeetingContent
from zope.component import adapter
from zope.interface import implementer
from zope.interface import Interface


@implementer(IExpandableElement)
@adapter(IMeetingContent, Interface)
class Annexes(object):
    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self, expand=False):
        result = {"annexes": {"@id": "{}/@annexes".format(self.context.absolute_url())}}
        if not expand:
            return result

        # extend batch? DEFAULT_BATCH_SIZE = 25
        # self.request.form['b_size'] = 50

        # get filters from request.form
        # it is possible to filter annexes on every boolean attributes :
        # to_print, confidential, publishable, to_sign/signed
        filters = {k: boolean_value(v) for k, v in self.request.form.items()
                   if k in ANNEXES_FILTER_VALUES}
        result = serialize_annexes(self.context, filters)
        return result


class AnnexesGet(Service):
    def reply(self):
        annexes = Annexes(self.context, self.request)
        return annexes(expand=True)
