# -*- coding: utf-8 -*-

from imio.restapi.services.search import SearchGet
from plone import api
from plone.restapi.deserializer import boolean_value
from plonemeeting.restapi.config import CONFIG_ID_ERROR
from plonemeeting.restapi.config import CONFIG_ID_NOT_FOUND_ERROR
from plonemeeting.restapi.config import INDEX_CORRESPONDENCES
from plonemeeting.restapi.utils import check_in_name_of
from zExceptions import BadRequest


class BaseSearchGet(SearchGet):
    """ """

    config_id_optional = True

    def __init__(self, context, request):
        """ """
        super(BaseSearchGet, self).__init__(context, request)
        self.tool = api.portal.get_tool("portal_plonemeeting")
        self.type = self._type
        self.config_id = self._config_id

    @property
    def _config_id(self):
        if not self.config_id_optional and \
           ("config_id" not in self.request.form and
                "getConfigId" not in self.request.form):
            raise BadRequest(CONFIG_ID_ERROR)
        return self.request.form.get("config_id") or \
            self.request.form.get("getConfigId")

    @property
    def _type(self):
        return self.request.form.get("type")

    def _set_query_before_hook(self):
        """ """
        query = {}
        form = self.request.form

        # fix getConfigId to be unable to search outside self.access_cfg_ids
        if self.access_cfg_ids:
            query['getConfigId'] = self.access_cfg_ids

        # turn convenience indexes names into real index names
        for real_index_name, easy_index_name in INDEX_CORRESPONDENCES.items():
            if easy_index_name in form:
                query[real_index_name] = form[easy_index_name]

        return query

    def reply(self):
        """Override to handle in_name_of."""
        self.in_name_of, self.access_cfg_ids = check_in_name_of(self.config_id, self.request.form)
        if self.in_name_of:
            # remove AUTHENTICATED_USER during adopt_user
            auth_user = self.request.get("AUTHENTICATED_USER")
            if auth_user:
                self.request["AUTHENTICATED_USER"] = None
            with api.env.adopt_user(username=self.in_name_of):
                res = self._process_reply()
            if auth_user:
                self.request["AUTHENTICATED_USER"] = auth_user
            return res
        else:
            return self._process_reply()

    def _clean_query(self, query):
        """Remove parameters that are not indexes names to avoid warnings like :
           WARNING plone.restapi.search.query No such index: 'extra_include'"""
        query.pop("extra_include", None)
        query.pop("in_name_of", None)
        for easy_index_name in INDEX_CORRESPONDENCES.values():
            query.pop(easy_index_name, None)


class PMSearchGet(BaseSearchGet):
    """Ease search of items and meetings related to a MeetingConfig.
       If config_id in REQUEST, we will configure some shortcuts,
       if not, the endpoint will behave as default."""

    def __init__(self, context, request):
        super(PMSearchGet, self).__init__(context, request)
        # if config_id is given, config_id must exist
        if self.config_id:
            self.cfg = self.tool.get(self.config_id, None)
            if not self.cfg:
                raise BadRequest(CONFIG_ID_NOT_FOUND_ERROR % self.config_id)

    @property
    def _config_id(self):
        config_id = self.request.form.get("config_id", None)
        in_name_of = self.request.form.get("in_name_of", None)
        # config_id or in_name_of is required when self.type is "item" or "meeting"
        if config_id is None and in_name_of is None and self.type in ["item", "meeting"]:
            raise BadRequest(CONFIG_ID_ERROR)
        return config_id

    @property
    def _type(self):
        # when using "config_id", default searched type is "item"
        if "type" not in self.request.form and \
           "config_id" in self.request.form:
            self.request.form["type"] = "item"
        return self.request.form.get("type")

    def _set_query_before_hook(self):
        query = super(PMSearchGet, self)._set_query_before_hook()
        query.update(self._set_query_meetings_accepting_items())
        return query

    def _set_query_meetings_accepting_items(self):
        """ """
        query = {}
        form = self.request.form
        if boolean_value(form.get("meetings_accepting_items", False)):
            # when using meetings_accepting_items, a config_id is required
            if not self.config_id:
                raise BadRequest(CONFIG_ID_ERROR)
            query.update(self.cfg._getMeetingsAcceptingItemsQuery())
            # we can call endpoint with just meetings_accepting_items=1
            self.type = "meeting"
        return query

    def _set_query_additional_params(self):
        """ """
        query = super(PMSearchGet, self)._set_query_additional_params()
        form = self.request.form
        if hasattr(self, "cfg") and self.cfg:
            mConfigs = [self.cfg]
        elif self.access_cfg_ids:
            mConfigs = [self.tool.get(e) for e in self.access_cfg_ids]

        # extend batch? DEFAULT_BATCH_SIZE = 25
        # self.request.form['b_size'] = 50

        # setup portal_type based on received 'type' parameter
        if self.type == "item":
            query["portal_type"] = [cfg.getItemTypeName() for cfg in mConfigs]
            query["sort_on"] = form.get("sort_on", "sortable_title")
        elif self.type == "meeting":
            query["portal_type"] = [cfg.getMeetingTypeName() for cfg in mConfigs]
            query["sort_on"] = form.get("sort_on", "sortable_title")
            query["sort_order"] = form.get("sort_order", "reverse")
            query["sort_on"] = form.get("sort_on", "sortable_title")
        elif self.type is not None:
            query["portal_type"] = self.type
            query["sort_on"] = form.get("sort_on", "sortable_title")
        return query

    def _clean_query(self, query):
        """See docstring in BaseSearchGet."""
        super(PMSearchGet, self)._clean_query(query)

        query.pop("additional_values", None)
        query.pop("base_search_uid", None)
        query.pop("meetings_accepting_items", None)

        # remove every values starting with include_ or extra_include_
        for k in query.keys():
            if k.startswith(('include_', 'extra_include_')):
                query.pop(k, None)
        # remove either "linkedMeetingUID" or "meeting_uid"
        catalog = self.context.portal_catalog
        if "linkedMeetingUID" in catalog.Indexes:
            query.pop("meeting_uid", None)
        else:
            query.pop("linkedMeetingUID", None)
