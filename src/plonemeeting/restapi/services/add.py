# -*- coding: utf-8 -*-

from collective.contact.plonegroup.utils import get_organizations
from collective.iconifiedcategory.utils import calculate_category_id
from imio.helpers.security import fplog
from imio.restapi.services.add import FolderPost
from plone import api
from plonemeeting.restapi.config import CONFIG_ID_ERROR
from plonemeeting.restapi.config import CONFIG_ID_NOT_FOUND_ERROR
from plonemeeting.restapi.utils import check_in_name_of
from Products.PloneMeeting.utils import add_wf_history_action
from Products.PloneMeeting.utils import org_id_to_uid
from zExceptions import BadRequest


ANNEX_CONTENT_CATEGORY_ERROR = 'Given content_category "%s" was not found!'
IGNORE_VALIDATION_FOR_REQUIRED_ERROR = \
    'You can not ignore validation for required fields! Define a value for %s!'
IGNORE_VALIDATION_FOR_VALUED_ERROR = \
    'You can not ignore validation of a field for which a value ' \
    'is provided, remove "%s" from data!'
IGNORE_VALIDATION_FOR_WARNING = 'Validation was ignored for following fields: %s.'
OPTIONAL_FIELD_ERROR = 'The optional field "%s" is not activated in this configuration! ' \
    'You can ignore optional fields errors by adding "ignore_not_used_data: true" to sent data.'
OPTIONAL_FIELDS_WARNING = 'The following optional fields are not activated in ' \
    'this configuration and were ignored: %s.'
ORG_FIELD_VALUE_ERROR = 'Error with value "%s" defined for field "%s"! Enter a valid organization id or UID.'
REQUIRED_FIELDS = ["title", "proposingGroup"]
UNKNOWN_DATA = "Following field names were ignored: %s"


class BasePost(FolderPost):
    def prepare_data(self, data):
        data = super(BasePost, self).prepare_data(data)

        # config_id
        self.tool = api.portal.get_tool("portal_plonemeeting")
        config_id = self._prepare_data_config_id(data)
        self.cfg = self.tool.get(config_id, None)
        if not self.cfg:
            raise Exception(CONFIG_ID_NOT_FOUND_ERROR % config_id)
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
                "in_name_of", None
            ):
                data["in_name_of"] = self.parent_data["in_name_of"]
            if data["@type"] == "annex":
                # turn annex_type into content_category
                content_category = data["content_category"]
                annex_type = self.cfg.annexes_types.item_annexes.get(content_category)
                if not annex_type:
                    raise BadRequest(ANNEX_CONTENT_CATEGORY_ERROR % content_category)
                annex_type_value = calculate_category_id(annex_type)
                data["content_category"] = annex_type_value

        return data

    def _prepare_data_config_id(self, data):
        if "config_id" not in data and "config_id" not in self.parent_data:
            raise Exception(CONFIG_ID_ERROR)
        return data.get("config_id", self.parent_data.get("config_id"))

    def _prepare_data_type(self, data):
        if "@type" not in data or "@type" == "item":
            data["@type"] = self.cfg.getItemTypeName()
        elif "@type" == "meeting":
            data["@type"] = self.cfg.getMeetingTypeName()
        return data.get("@type")

    def _process_reply(self):
        # change context, the view is called on portal, when need
        # the set context to place where element will be added
        # if we have something else, probably we are adding an annex into an item or meeting
        if self.context.portal_type == "Plone Site":
            self.context = self.tool.getPloneMeetingFolder(self.cfg.getId())
        serialized_obj = super(BasePost, self)._reply()
        self._check_unknown_data(serialized_obj)
        return serialized_obj

    def _reply(self):
        in_name_of = check_in_name_of(self, self.data)
        if in_name_of:
            with api.env.adopt_user(username=in_name_of):
                return self._process_reply()
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
                REQUIRED_FIELDS)
            if ignored_required_fields:
                raise BadRequest(IGNORE_VALIDATION_FOR_REQUIRED_ERROR % u", ".join(
                    ignored_required_fields))

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
        org_uids = get_organizations(only_selected=False, the_objects=False)

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
        ignored = ["ignore_validation_for"]
        diff = set(self.cleaned_data.keys()).difference(serialized_obj.keys() + ignored)
        if diff:
            self.warnings.append(UNKNOWN_DATA % ", ".join(diff))


class ItemPost(BasePost):
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


class MeetingPost(BasePost):
    @property
    def _optional_fields(self):
        return self.cfg.listUsedMeetingAttributes()

    @property
    def _active_fields(self):
        return self.cfg.getUsedMeetingAttributes()
