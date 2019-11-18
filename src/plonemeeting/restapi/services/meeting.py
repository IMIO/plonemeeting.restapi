# -*- coding: utf-8 -*-

from plone import api
from plone.restapi.services.search.get import SearchGet


class BaseSearchMeetingGet(SearchGet):

    def __init__(self, context, request):
        super(BaseSearchMeetingGet, self).__init__(context, request)
        self.tool = api.portal.get_tool('portal_plonemeeting')
        config_id = self._config_id
        self.cfg = self.tool.get(config_id, None)
        if not self.cfg:
            raise Exception(
                "The given \"getConfigId\" named \"{0}\" was not found".format(
                    config_id)
            )

    @property
    def _additional_fields(self):
        ''' '''
        return ['UID']

    @property
    def _config_id(self):
        if 'getConfigId' not in self.request.form:
            raise Exception(
                "The \"getConfigId\" parameter must be given"
            )
        return self.request.form.get('getConfigId')

    def _set_additional_query_params(self):
        ''' '''
        form = self.request.form
        form['portal_type'] = self.cfg.getMeetingTypeName()
        form['metadata_fields'] = form.get('metadata_fields', []) + \
            self._additional_fields
        form['fullobjects'] = True

    def reply(self):
        self._set_additional_query_params()
        return super(BaseSearchMeetingGet, self).reply()


class SearchMeetingsGet(BaseSearchMeetingGet):
    ''' '''

    def _set_additional_query_params(self):
        super(SearchMeetingsGet, self)._set_additional_query_params()
        form = self.request.form
        form['sort_on'] = form.get('sort_on', 'sortable_title')


class SearchMeetingItemsGet(BaseSearchMeetingGet):

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
