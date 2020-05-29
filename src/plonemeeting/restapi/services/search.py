# -*- coding: utf-8 -*-

from plone import api
from plone.restapi.services.search.get import SearchGet
from plone.restapi.search.handler import SearchHandler
from plone.restapi.search.utils import unflatten_dotted_dict
from plonemeeting.restapi.utils import listify


class PMSearchGet(SearchGet):

    def __init__(self, context, request):
        super(PMSearchGet, self).__init__(context, request)
        self.tool = api.portal.get_tool('portal_plonemeeting')
        config_id = self._config_id
        self.type = self._type
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
        if 'config_id' not in self.request.form:
            raise Exception(
                "The \"config_id\" parameter must be given"
            )
        return self.request.form.get('config_id')

    @property
    def _type(self):
        if 'type' not in self.request.form:
            self.request.form['type'] = 'item'
        return self.request.form.get('type')

    def _set_additional_query_params(self):
        ''' '''
        form = self.request.form

        # config_id is actually the getConfigId index
        form['getConfigId'] = form['config_id']

        # manage metadata_fields
        additional_metadata_fields = listify(form.get("metadata_fields", []))
        additional_metadata_fields += self._additional_fields
        form['metadata_fields'] = additional_metadata_fields

        # extend batch? DEFAULT_BATCH_SIZE = 25
        # self.request.form['b_size'] = 50

        # setup portal_type based on received 'type' parameter
        if self.type == 'item':
            form['portal_type'] = self.cfg.getItemTypeName()
            form['sort_on'] = form.get('sort_on', 'sortable_title')
        elif self.type == 'meeting':
            form['portal_type'] = self.cfg.getMeetingTypeName()
            form['sort_on'] = form.get('sort_on', 'sortable_title')
            form['sort_order'] = form.get('sort_order', 'reverse')

    def _clean_query(self, query):
        """Remove parameters that are not indexes names to avoid warnings like :
           WARNING plone.restapi.search.query No such index: 'extra_include'"""
        query.pop('config_id', None)
        query.pop('type', None)
        query.pop('extra_include', None)

    def reply(self):
        self._set_additional_query_params()
        query = self.request.form.copy()
        self._clean_query(query)
        query = unflatten_dotted_dict(query)

        return SearchHandler(self.context, self.request).search(query)
