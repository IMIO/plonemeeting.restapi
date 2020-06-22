# -*- coding: utf-8 -*-

from collective.iconifiedcategory.utils import get_categorized_elements
from plone.restapi.interfaces import IExpandableElement
from plone.restapi.interfaces import ISerializeToJson
from plone.restapi.services import Service
from Products.PloneMeeting.interfaces import IMeetingContent
from zope.component import adapter
from zope.component import getMultiAdapter
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

        annexes = get_categorized_elements(self.context, result_type="objects")
        result = []
        for annex in annexes:
            serialized_annex = getMultiAdapter(
                (annex, self.request), ISerializeToJson
            )()
            result.append(serialized_annex)
        return result


class AnnexesGet(Service):
    def reply(self):
        annexes = Annexes(self.context, self.request)
        return annexes(expand=True)
