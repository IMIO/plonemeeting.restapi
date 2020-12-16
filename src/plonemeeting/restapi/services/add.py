# -*- coding: utf-8 -*-

from collective.iconifiedcategory.utils import calculate_category_id
from imio.helpers.security import fplog
from imio.restapi.services.add import FolderPost
from plone import api
from plone.restapi.deserializer import json_body
from plonemeeting.restapi.config import CONFIG_ID_ERROR
from plonemeeting.restapi.config import CONFIG_ID_NOT_FOUND_ERROR
from plonemeeting.restapi.utils import check_in_name_of
from Products.PloneMeeting.utils import add_wf_history_action
from Products.PloneMeeting.utils import org_id_to_uid
from zExceptions import BadRequest


OPTIONAL_FIELD_ERROR = 'The optional field "%s" is not activated in this configuration!'
ANNEX_CONTENT_CATEGORY_ERROR = 'Given content_category "%s" was not found!'


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
            # turn ids to UIDs
            data = self._turn_ids_into_uids(data)
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
    def _data(self):
        return json_body(self.request)

    @property
    def _optional_fields(self):
        return []

    @property
    def _active_fields(self):
        return []

    def _check_optional_fields(self, data):
        optional_fields = self._optional_fields
        active_fields = self._active_fields
        for field_name, field_value in data.items():
            # if the field is an optional field that is not used
            # and that has a value (contains data), we raise
            if (
                field_name in optional_fields
                and field_name not in active_fields
                and field_value
            ):
                raise BadRequest(OPTIONAL_FIELD_ERROR % field_name)
        return data

    @property
    def _turn_ids_into_uids_fieldnames(self):
        return []

    def _turn_ids_into_uids(self, data):
        for field_name in self._turn_ids_into_uids_fieldnames:
            field_value = data.get(field_name)
            if field_value:
                if hasattr(field_value, "__iter__"):
                    data[field_name] = [
                        org_id_to_uid(v, raise_on_error=False) or v
                        for v in field_value
                        if v
                    ]
                else:
                    data[field_name] = (
                        org_id_to_uid(field_value, raise_on_error=False) or field_value
                    )
        return data

    def clean_data(self, data):
        """Remove parameters that are not attributes."""
        cleaned_data = super(BasePost, self).clean_data(data)
        cleaned_data.pop("config_id", None)
        cleaned_data.pop("in_name_of", None)
        cleaned_data.pop("wf_transitions", None)
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
        diff = set(self.cleaned_data.keys()).difference(serialized_obj.keys())
        if diff:
            unkown_msg = "Following field names were ignored : %s" % ", ".join(diff)
            self.warnings.append(unkown_msg)


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
