# -*- coding: utf-8 -*-

from collective.contact.plonegroup.utils import get_organizations
from collective.iconifiedcategory.utils import calculate_category_id
from imio.helpers.content import get_vocab
from imio.helpers.security import fplog
from imio.restapi.services.add import FolderPost
from imio.restapi.utils import get_return_fullobject_after_creation_default
from plone import api
from plonemeeting.restapi.config import CONFIG_ID_ERROR
from plonemeeting.restapi.config import CONFIG_ID_NOT_FOUND_ERROR
from plonemeeting.restapi.services.get import _get_obj_from_uid
from plonemeeting.restapi.utils import check_in_name_of
from Products.PloneMeeting.utils import add_wf_history_action
from Products.PloneMeeting.utils import get_annexes_config
from Products.PloneMeeting.utils import org_id_to_uid
from zExceptions import BadRequest
from zope.component import queryMultiAdapter
from zope.interface import implementer
from zope.publisher.interfaces import IPublishTraverse
from zope.publisher.interfaces import NotFound


ANNEX_CONTENT_CATEGORY_ERROR = 'Given content_category "%s" was not found or ' \
    'is not useable for the annex you try to add!'
ANNEX_DECISION_RELATED_NOT_ITEM_ERROR = 'The "decision_related" parameter is ' \
    'only relevant when annex added on an item!'
ANNEX_NO_CONTENT_CATEGORY_AVAILABLE_ERROR = 'No annex_type available to create annex, ' \
    'please check configuration!'
IGNORE_VALIDATION_FOR_REQUIRED_ERROR = \
    'You can not ignore validation for following required fields: "%s"!'
IGNORE_VALIDATION_FOR_VALUED_ERROR = \
    'You can not ignore validation of a field for which a value ' \
    'is provided, remove "%s" from data!'
IGNORE_VALIDATION_FOR_WARNING = 'Validation was ignored for following fields: %s.'
OPTIONAL_FIELD_ERROR = 'The optional field "%s" is not activated in this configuration! ' \
    'You can ignore optional fields errors by adding "ignore_not_used_data: true" to sent data.'
OPTIONAL_FIELDS_WARNING = 'The following optional fields are not activated in ' \
    'this configuration and were ignored: %s.'
ORG_FIELD_VALUE_ERROR = 'Error with value "%s" defined for field "%s"! Enter a valid organization id or UID.'
UNKNOWN_DATA = "Following field names were ignored: %s."


class BasePost(FolderPost):

    # to be overrided
    required_fields = []

    def prepare_data(self, data):
        data = super(BasePost, self).prepare_data(data)

        # config_id
        self.tool = api.portal.get_tool("portal_plonemeeting")
        config_id = self._prepare_data_config_id(data)
        self.cfg = self.tool.get(config_id, None)
        if not self.cfg:
            raise BadRequest(CONFIG_ID_NOT_FOUND_ERROR % config_id)
        # type
        self.type = self._prepare_data_type(data)
        # main checks
        if data["@type"].startswith("Meeting"):
            # check that given values are useable, will raise if not
            data = self._check_optional_fields(data)
            # check fields for which validation will be ignored
            data = self._check_ignore_validation_for(data)
            # turn ids to UIDs
            data = self._turn_ids_into_uids(data)
            # fix data
            data = self._fix_data(data)
        elif data["@type"].startswith("annex"):
            # reinject data from parent: config_id and in_name_of
            data["config_id"] = self.cfg.getId()
            if not data.get("in_name_of", None) and self.parent_data.get(
               "in_name_of", None):
                data["in_name_of"] = self.parent_data["in_name_of"]
            # when adding a single annex, self is an AnnexPost instance
            # when adding an item with __children__ annexes it is not
            # the case but we use the _turn_ids_into_uids from AnnexPost
            # to cleanup data
            annex_post = self
            if not isinstance(annex_post, AnnexPost):
                portal = api.portal.get()
                annex_post = queryMultiAdapter(
                    (portal, self.request),
                    name="POST_application_json_@annex")
                annex_post._container = self.context
                annex_post.context = self.context
            data = annex_post._turn_ids_into_uids(data)
        return data

    def _prepare_data_config_id(self, data):
        if "config_id" not in data and "config_id" not in self.parent_data:
            raise BadRequest(CONFIG_ID_ERROR)
        return data.get("config_id", self.parent_data.get("config_id"))

    def _get_container(self):
        """ """
        return self.tool.getPloneMeetingFolder(self.cfg.getId())

    def _process_reply(self):
        # change context, the view is called on portal, when need
        # the set context to place where element will be added
        # if we have something else, probably we are adding an annex into an item or meeting
        if self.context.portal_type == "Plone Site":
            self.context = self._get_container()
        serialized_obj = super(BasePost, self)._reply()
        self._check_unknown_data(serialized_obj)
        return serialized_obj

    def _reply(self):
        in_name_of = check_in_name_of(self, self.data)
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

    @property
    def _optional_fields(self):
        return []

    @property
    def _active_fields(self):
        return []

    def _check_optional_fields(self, data):
        optional_fields = self._optional_fields
        active_fields = self._active_fields
        inactive_fields = []
        ignore_not_used_data = data.get("ignore_not_used_data", False)
        for field_name, field_value in data.items():
            # if the field is an optional field that is not used
            # and that has a value (contains data), we warn if
            # ignore_not_used_data or we raise
            if (
                field_name in optional_fields
                and field_name not in active_fields
                and field_value
            ):
                if ignore_not_used_data:
                    inactive_fields.append(field_name)
                    data.pop(field_name)
                else:
                    raise BadRequest(OPTIONAL_FIELD_ERROR % field_name)

        if inactive_fields:
            self.warnings.append(OPTIONAL_FIELDS_WARNING %
                                 u', '.join(inactive_fields))
        return data

    def _check_ignore_validation_for(self, data):
        """Parameter "ignore_validation_for" will let ignore validation
           of given fields for which no value was provided."""
        ignore_validation_for = data.get("ignore_validation_for", [])
        if ignore_validation_for:
            # raise if trying to ignore validation of a required field
            ignored_required_fields = set(ignore_validation_for).intersection(
                self.required_fields)
            if ignored_required_fields:
                raise BadRequest(IGNORE_VALIDATION_FOR_REQUIRED_ERROR % u", ".join(
                    self.required_fields))

            # raise if trying to bypass validation and a value is given
            ignored_valued_fields = [k for k, v in data.items()
                                     if k in ignore_validation_for and v]
            if ignored_valued_fields:
                raise BadRequest(IGNORE_VALIDATION_FOR_VALUED_ERROR % u", ".join(
                    ignored_valued_fields))

            self.warnings.append(IGNORE_VALIDATION_FOR_WARNING %
                                 u', '.join(ignore_validation_for))
            # remove these fields from data to avoid setting a wrong empty value
            for field_name in ignore_validation_for:
                data.pop(field_name, None)
        return data

    @property
    def _turn_ids_into_uids_fieldnames(self):
        return []

    def _turn_ids_into_uids(self, data):
        # this will also include organizations outside "My org"
        org_uids = get_vocab(
            self.cfg,
            "Products.PloneMeeting.vocabularies.everyorganizationsvocabulary").by_token

        def _get_org_uid(field_name, field_value):
            """Get org UID as given field_value may be an UID or an id."""

            if field_value in org_uids:
                return field_value
            else:
                org_uid = org_id_to_uid(field_value, raise_on_error=False)
                if org_uid is None:
                    raise BadRequest(ORG_FIELD_VALUE_ERROR % (field_value, field_name))
                return org_uid

        for field_name in self._turn_ids_into_uids_fieldnames:
            field_value = data.get(field_name)
            if field_value:
                if hasattr(field_value, "__iter__"):
                    data[field_name] = []
                    for v in field_value:
                        data[field_name].append(_get_org_uid(field_name, v))
                else:
                    data[field_name] = _get_org_uid(field_name, field_value)
        return data

    def _fix_data(self, data):
        """Fix some data format."""
        # externalIdentifier must be string
        if "externalIdentifier" in data:
            externalIdentifier = data["externalIdentifier"]
            externalIdentifier = externalIdentifier and str(externalIdentifier) or ""
            data["externalIdentifier"] = externalIdentifier
        return data

    def clean_data(self, data):
        """Remove parameters that are not attributes."""
        cleaned_data = super(BasePost, self).clean_data(data)
        cleaned_data.pop("config_id", None)
        cleaned_data.pop("in_name_of", None)
        cleaned_data.pop("wf_transitions", None)
        cleaned_data.pop("ignore_not_used_data", None)
        cleaned_data.pop("decision_related", None)
        return cleaned_data

    def _after_reply_hook(self, serialized_obj):
        """ """
        obj = self.context.get(serialized_obj["id"])
        # add a record to the item workflow_history to specify that item was created thru SOAP WS
        action_name = "create_element_using_ws_rest"
        action_label = action_name + "_comments"
        # there may be several actions in the workflow_history, especially when
        # wf_transitions are used so we insert our event just after event 0
        add_wf_history_action(obj,
                              action_name=action_name,
                              action_label=action_label,
                              insert_index=0)
        # fingerpointing
        extras = "object={0}".format(repr(self.context.get(serialized_obj["id"])))
        fplog("create_by_ws_rest", extras=extras)

    def _check_unknown_data(self, serialized_obj):
        ignored = ["ignore_validation_for", "clean_html"]
        # if we have the full serialized obj, then we may check unknown data
        diff = []
        if get_return_fullobject_after_creation_default():
            diff = set(self.cleaned_data.keys()).difference(
                serialized_obj.keys() + ignored)
        if diff:
            self.warnings.append(UNKNOWN_DATA % ", ".join(diff))


class ItemPost(BasePost):

    required_fields = ["title", "proposingGroup"]

    @property
    def _turn_ids_into_uids_fieldnames(self):
        return [
            "proposingGroup",
            "groupsInCharge",
            "associatedGroups",
            "optionalAdvisers",
        ]

    @property
    def _optional_fields(self):
        return self.cfg.listUsedItemAttributes()

    @property
    def _active_fields(self):
        return self.cfg.getUsedItemAttributes()

    def _wf_transition_additional_warning(self, tr):
        warning_message = ""
        if tr == "present":
            warning_message = (
                " Make sure a meeting accepting items "
                "exists in configuration '{0}'!".format(self.cfg.getId())
            )
        return warning_message

    def _prepare_data_type(self, data):
        if not data.get("@type"):
            data["@type"] = self.cfg.getItemTypeName()
        return data.get("@type")


class MeetingPost(BasePost):

    required_fields = ["date"]

    @property
    def _optional_fields(self):
        return self.cfg.listUsedMeetingAttributes()

    @property
    def _active_fields(self):
        return self.cfg.getUsedMeetingAttributes()

    def _prepare_data_type(self, data):
        if not data.get("@type"):
            data["@type"] = self.cfg.getMeetingTypeName()
        return data.get("@type")


@implementer(IPublishTraverse)
class AnnexPost(BasePost):

    def __init__(self, context, request):
        super(AnnexPost, self).__init__(context, request)
        self.container_uid = None
        self._container = None

    def publishTraverse(self, request, name):
        if self.container_uid is None:
            self.container_uid = name
        else:
            raise NotFound(self, name, request)
        return self

    @property
    def container(self):
        if not self._container:
            self._container = _get_obj_from_uid(self.container_uid)
            self.context = self._container
        return self.context

    def _get_container(self):
        """ """
        return self.context

    def _prepare_data_config_id(self, data):
        tool = api.portal.get_tool("portal_plonemeeting")
        cfg = tool.getMeetingConfig(self.container)
        return cfg.getId()

    def _prepare_data_type(self, data):
        decision_related = data.get("decision_related", False)
        if decision_related and not self._container.__class__.__name__ == "MeetingItem":
            raise BadRequest(ANNEX_DECISION_RELATED_NOT_ITEM_ERROR)
        data["@type"] = decision_related and "annexDecision" or "annex"
        return data.get("@type")

    def _turn_ids_into_uids(self, data):
        # turn annex_type id into content_category calculated id
        content_category = data.get("content_category", None)
        annex_type = None
        # get selectable categories
        if data["@type"] == "annexDecision":
            self.request.set('force_use_item_decision_annexes_group', True)
        vocab = get_vocab(self.context, 'collective.iconifiedcategory.categories')
        # when content_category provided, it must exist
        if content_category is not None:
            annex_group = get_annexes_config(self.context, data["@type"], annex_group=True)
            # get given content_category or the first one
            annex_type = annex_group.get(content_category)
            if not annex_type:
                raise BadRequest(ANNEX_CONTENT_CATEGORY_ERROR % content_category)
            annex_type_value = calculate_category_id(annex_type)
            if annex_type_value not in vocab:
                raise BadRequest(ANNEX_CONTENT_CATEGORY_ERROR % content_category)
        else:
            # use the default annex_type, the first selectable
            if not vocab._terms:
                raise BadRequest(ANNEX_NO_CONTENT_CATEGORY_AVAILABLE_ERROR)
            annex_type_value = vocab._terms[0].token
        data["content_category"] = annex_type_value
        # cleanup
        if data["@type"] == "annexDecision":
            self.request.set('force_use_item_decision_annexes_group', False)

        return data
