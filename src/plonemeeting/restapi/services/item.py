# -*- coding: utf-8 -*-

from plone.restapi.interfaces import IExpandableElement
from plone.restapi.interfaces import ISerializeToJson
from plone.restapi.services import Service
from plonemeeting.restapi.services.base import BaseSearchGet
from Products.PloneMeeting.interfaces import IMeetingItem
from zope.component import adapter
from zope.component import getMultiAdapter
from zope.interface import implementer
from zope.interface import Interface


class SearchItemsGet(BaseSearchGet):
    ''' '''

    def _set_additional_query_params(self):
        super(SearchItemsGet, self)._set_additional_query_params()
        form = self.request.form
        form['portal_type'] = self.cfg.getItemTypeName()
        form['sort_on'] = form.get('sort_on', 'sortable_title')


@implementer(IExpandableElement)
@adapter(IMeetingItem, Interface)
class ItemDeliberationInfos(object):
    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self, expand=False):
        result = {"deliberation": {"@id": "{}/@deliberation".format(self.context.absolute_url())}}
        if not expand:
            return result

        result = {}
        result = getMultiAdapter(
            (self.context, self.request), ISerializeToJson).deliberation()
        return result


class ItemDeliberationInfosGet(Service):
    def reply(self):
        item_deliberation_infos = ItemDeliberationInfos(self.context, self.request)
        return item_deliberation_infos(expand=True)
