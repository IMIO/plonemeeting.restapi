# -*- coding: utf-8 -*-

from imio.restapi.services.search import SearchGet
from plone import api
from plone.restapi.deserializer import boolean_value
from plonemeeting.restapi.config import CONFIG_ID_ERROR
from plonemeeting.restapi.config import CONFIG_ID_NOT_FOUND_ERROR
from plonemeeting.restapi.utils import check_in_name_of


class PMSearchGet(SearchGet):
    """Ease search of items and meetings related to a MeetingConfig.
       If config_id in REQUEST, we will configure some shortcuts,
       if not, the endpoint will behave as default."""

    def __init__(self, context, request):
        super(PMSearchGet, self).__init__(context, request)
        self.tool = api.portal.get_tool("portal_plonemeeting")
        self.type = self._type
        config_id = self._config_id
        # if config_id is given, config_id must exist
        if config_id:
            self.cfg = self.tool.get(config_id, None)
            if not self.cfg:
                raise Exception(CONFIG_ID_NOT_FOUND_ERROR % config_id)

    @property
    def _config_id(self):
        config_id = self.request.form.get("config_id", None)
        # config_id is required when self.type is "item" or "meeting"
        if config_id is None and self.type in ["item", "meeting"]:
            raise Exception(CONFIG_ID_ERROR)
        return config_id

    @property
    def _type(self):
        # when using "config_id", default searched type is "item"
        if "type" not in self.request.form and \
           "config_id" in self.request.form:
            self.request.form["type"] = "item"
        return self.request.form.get("type")

    def _set_query_before_hook(self):
        return self._set_query_meetings_accepting_items()

    def _set_query_meetings_accepting_items(self):
        """ """
        query = {}
        form = self.request.form
        if self.type == "meeting" and boolean_value(
            form.get("meetings_accepting_items", False)
        ):
            query.update(self.cfg._getMeetingsAcceptingItemsQuery())
        return query

    def _set_query_additional_params(self):
        """ """
        query = {}
        form = self.request.form

        # config_id is actually the getConfigId index
        if "config_id" in form:
            query["getConfigId"] = form["config_id"]

        # extend batch? DEFAULT_BATCH_SIZE = 25
        # self.request.form['b_size'] = 50

        # setup portal_type based on received 'type' parameter
        if self.type == "item":
            query["portal_type"] = self.cfg.getItemTypeName()
            query["sort_on"] = form.get("sort_on", "sortable_title")
        elif self.type == "meeting":
            query["portal_type"] = self.cfg.getMeetingTypeName()
            query["sort_on"] = form.get("sort_on", "sortable_title")
            query["sort_order"] = form.get("sort_order", "reverse")
        elif self.type is not None:
            query["portal_type"] = self.type
            query["sort_on"] = form.get("sort_on", "sortable_title")
        return query

    def _clean_query(self, query):
        """Remove parameters that are not indexes names to avoid warnings like :
           WARNING plone.restapi.search.query No such index: 'extra_include'"""
        query.pop("additional_values", None)
        query.pop("base_search_uid", None)
        query.pop("config_id", None)
        query.pop("extra_include", None)
        query.pop("in_name_of", None)
        query.pop("meetings_accepting_items", None)
        query.pop("type", None)
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

    def reply(self):
        """Override to handle in_name_of."""
        in_name_of = check_in_name_of(self, self.request.form)
        if in_name_of:
            # remove AUTHENTICATED_USER during adopt_user
            auth_user = self.request.get("AUTHENTICATED_USER")
            if auth_user:
                self.request["AUTHENTICATED_USER"] = None
            with api.env.adopt_user(username=in_name_of):
                res = self._process_reply()
            if auth_user:
                self.request["AUTHENTICATED_USER"] = auth_user
            return res
        else:
            return self._process_reply()
