# -*- coding: utf-8 -*-

from plone import api
from plone.restapi.services.search.get import SearchGet
from plonemeeting.restapi.utils import listify


class BaseSearchGet(SearchGet):

    def __init__(self, context, request):
        super(BaseSearchGet, self).__init__(context, request)
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

        additional_metadata_fields = listify(form.get("metadata_fields", []))
        additional_metadata_fields += self._additional_fields
        form['metadata_fields'] = additional_metadata_fields

        # extend batch? DEFAULT_BATCH_SIZE = 25
        # self.request.form['b_size'] = 50

    def reply(self):
        self._set_additional_query_params()
        return super(BaseSearchGet, self).reply()
