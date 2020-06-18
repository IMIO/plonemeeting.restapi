# -*- coding: utf-8 -*-

from imio.helpers.content import uuidsToObjects
from plone import api
from plone.app.querystring.queryparser import parseFormquery
from plone.restapi.deserializer import boolean_value
from plone.restapi.search.handler import SearchHandler
from plone.restapi.search.utils import unflatten_dotted_dict
from plone.restapi.services.search.get import SearchGet
from plonemeeting.restapi.config import CONFIG_ID_ERROR
from plonemeeting.restapi.config import CONFIG_ID_NOT_FOUND_ERROR
from plonemeeting.restapi.utils import check_in_name_of
from plonemeeting.restapi.utils import listify


class PMSearchGet(SearchGet):
    def __init__(self, context, request):
        super(PMSearchGet, self).__init__(context, request)
        self.tool = api.portal.get_tool("portal_plonemeeting")
        config_id = self._config_id
        self.type = self._type
        self.cfg = self.tool.get(config_id, None)
        if not self.cfg:
            raise Exception(CONFIG_ID_NOT_FOUND_ERROR % config_id)

    @property
    def _additional_fields(self):
        """ """
        return ["UID"]

    @property
    def _config_id(self):
        if "config_id" not in self.request.form:
            raise Exception(CONFIG_ID_ERROR)
        return self.request.form.get("config_id")

    @property
    def _type(self):
        if "type" not in self.request.form:
            self.request.form["type"] = "item"
        return self.request.form.get("type")

    def _set_query_base_search(self):
        """ """
        query = {}
        form = self.request.form
        base_search_uid = form.get("base_search_uid", "").strip()
        if base_search_uid:
            collection = uuidsToObjects(uuids=base_search_uid)
            if collection:
                collection = collection[0]
                query = parseFormquery(collection, collection.query)
        return query

    def _set_query_meetings_accepting_items(self):
        """ """
        query = {}
        form = self.request.form
        if self.type == "meeting" and boolean_value(form.get("meetings_accepting_items", False)):
            query.update(self.cfg._getMeetingsAcceptingItemsQuery())
        return query

    def _set_query_additional_params(self):
        """ """
        query = {}
        form = self.request.form

        # config_id is actually the getConfigId index
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
        return query

    def _clean_query(self, query):
        """Remove parameters that are not indexes names to avoid warnings like :
           WARNING plone.restapi.search.query No such index: 'extra_include'"""
        query.pop("base_search_uid", None)
        query.pop("config_id", None)
        query.pop("extra_include", None)
        query.pop("in_name_of", None)
        query.pop("meetings_accepting_items", None)
        query.pop("type", None)

    def _set_metadata_fields(self):
        """Must be set in request.form."""
        form = self.request.form
        # manage metadata_fields
        additional_metadata_fields = listify(form.get("metadata_fields", []))
        additional_metadata_fields += self._additional_fields
        form["metadata_fields"] = additional_metadata_fields

    def _process_reply(self):
        query = {}

        query.update(self._set_query_meetings_accepting_items())
        query.update(self._set_query_base_search())
        query.update(self._set_query_additional_params())
        query.update(self.request.form.copy())
        self._clean_query(query)
        query = unflatten_dotted_dict(query)

        self._set_metadata_fields()

        return SearchHandler(self.context, self.request).search(query)

    def reply(self):
        in_name_of = check_in_name_of(self, self.request.form)
        if in_name_of:
            with api.env.adopt_user(username=in_name_of):
                return self._process_reply()
        else:
            return self._process_reply()
