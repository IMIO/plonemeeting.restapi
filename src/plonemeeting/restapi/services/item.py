# -*- coding: utf-8 -*-

from plonemeeting.restapi.services.base import BaseSearchGet


class SearchItemsGet(BaseSearchGet):
    ''' '''

    def _set_additional_query_params(self):
        super(SearchItemsGet, self)._set_additional_query_params()
        form = self.request.form
        form['portal_type'] = self.cfg.getItemTypeName()
        form['sort_on'] = form.get('sort_on', 'sortable_title')
