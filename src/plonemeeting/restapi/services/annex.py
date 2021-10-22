# -*- coding: utf-8 -*-

from collective.iconifiedcategory.utils import get_categorized_elements
from plone.restapi.deserializer import boolean_value
from plone.restapi.interfaces import IExpandableElement
from plone.restapi.services import Service
from plonemeeting.restapi.utils import get_serializer
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

        annexes = get_categorized_elements(self.context, result_type="objects")
        result = []
        # get filters from request.form
        # it is possible to filter annexes on every boolean attributes :
        # to_print, confidential, publishable, to_sign/signed
        filters = {k: boolean_value(v) for k, v in self.request.form.items()
                   if k in ["to_print", "confidential", "publishable",
                            "to_sign", "signed"]}
        for annex in annexes:
            # check filters
            keep = True
            for k, v in filters.items():
                if getattr(annex, k, None) != v:
                    keep = False
                    break
            if not keep:
                continue
            serializer = get_serializer(annex)
            serialized_annex = serializer()
            result.append(serialized_annex)
        return result


class AnnexesGet(Service):
    def reply(self):
        annexes = Annexes(self.context, self.request)
        return annexes(expand=True)
