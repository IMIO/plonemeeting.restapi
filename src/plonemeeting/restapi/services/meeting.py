# -*- coding: utf-8 -*-

from plonemeeting.restapi.services.base import BaseSearchGet


class SearchMeetingsGet(BaseSearchGet):
    ''' '''

    def _set_additional_query_params(self):
        super(SearchMeetingsGet, self)._set_additional_query_params()
        form = self.request.form
        form['portal_type'] = self.cfg.getMeetingTypeName()
        form['sort_on'] = form.get('sort_on', 'sortable_title')
        form['sort_order'] = form.get('sort_order', 'reverse')
