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


class SearchMeetingItemsGet(BaseSearchGet):

    @property
    def _meeting_uid(self):
        if 'linkedMeetingUID' not in self.request.form:
            raise Exception(
                "The \"linkedMeetingUID\" parameter must be given"
            )
        return self.request.form.get('linkedMeetingUID')

    @property
    def _additional_fields(self):
        ''' '''
        fields = super(SearchMeetingItemsGet, self)._additional_fields
        fields += ['itemNumber']
        return fields

    def _set_additional_query_params(self):
        super(SearchMeetingItemsGet, self)._set_additional_query_params()
        form = self.request.form
        form['linkedMeetingUID'] = self._meeting_uid
        form['portal_type'] = self.cfg.getItemTypeName()
        form['sort_on'] = form.get('sort_on', 'getItemNumber')
