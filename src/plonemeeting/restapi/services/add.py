# -*- coding: utf-8 -*-

from AccessControl import Unauthorized
from collective.iconifiedcategory.utils import calculate_category_id
from Products.PloneMeeting.utils import add_wf_history_action
from imio.restapi.services.add import FolderPost
from plone import api
from plone.restapi.deserializer import json_body
from Products.PloneMeeting.utils import org_id_to_uid
from zExceptions import BadRequest

import json

OPTIONAL_FIELD_ERROR = "The optional field \"%s\" is not activated in this configuration!"


class BasePost(FolderPost):

    def __init__(self, context, request):
        super(BasePost, self).__init__(context, request)
        # some variables
        self.tool = api.portal.get_tool('portal_plonemeeting')
        self.data = self._data
        config_id = self._config_id
        self.cfg = self.tool.get(config_id, None)
        if not self.cfg:
            raise Exception(
                "The given \"config_id\" named \"{0}\" was not found".format(
                    config_id)
            )
        self.type = self._type
        self.warnings = []

    def _reply(self):
        serialized_obj = super(BasePost, self).reply()
        self._check_unknown_data(serialized_obj)
        serialized_obj['@warnings'] = self.warnings
        return serialized_obj

    def reply(self):
        self.cleaned_data = self.clean_data()

        # set new BODY with cleaned data
        self.request.set('BODY', json.dumps(self.cleaned_data))

        in_name_of = self.data.get('in_name_of', None)
        # change context, the view is called on portal, when need
        # the set context to place where element will be added
        # if we have something else, probably we are adding an annex into an item or meeting
        if self.context.portal_type == 'Plone Site':
            self.context = self.tool.getPloneMeetingFolder(self.cfg.getId(), userId=in_name_of)
        if in_name_of:
            self._check_in_name_of()
            with api.env.adopt_user(username=in_name_of):
                return self._reply()
        else:
            return self._reply()

    def _check_in_name_of(self):
        if not bool(self.tool.isManager(self.context)):
            raise Unauthorized

    @property
    def _config_id(self):
        if 'config_id' not in self.data:
            raise Exception(
                "The \"config_id\" parameter must be given"
            )
        return self.data.get('config_id')

    @property
    def _type(self):
        if '@type' not in self.data or '@type' == 'item':
            self.data['@type'] = self.cfg.getItemTypeName()
        elif '@type' == 'meeting':
            self.data['@type'] = self.cfg.getMeetingTypeName()
        return self.data.get('@type')

    @property
    def _data(self):
        return json_body(self.request)

    @property
    def _optional_fields(self):
        return []

    @property
    def _active_fields(self):
        return []

    def _check_optional_fields(self):
        optional_fields = self._optional_fields
        active_fields = self._active_fields
        for field_name, field_value in self.data.items():
            # if the field is an optional field that is not used
            # and that has a value (contains data), we raise
            if field_name in optional_fields and \
               field_name not in active_fields and \
               field_value:
                raise BadRequest(OPTIONAL_FIELD_ERROR % field_name)

    @property
    def _turn_ids_into_uids_fieldnames(self):
        return []

    def _turn_ids_into_uids(self):
        for field_name in self._turn_ids_into_uids_fieldnames:
            field_value = self.data.get(field_name)
            if field_value:
                if hasattr(field_value, '__iter__'):
                    self.data[field_name] = [org_id_to_uid(v, raise_on_error=False) or v
                                             for v in field_value if v]
                else:
                    self.data[field_name] = \
                        org_id_to_uid(field_value, raise_on_error=False) or field_value

    def _prepare_data(self, data):
        if data['@type'].startswith('Meeting'):
            # check that given values are useable, will raise if not
            self._check_optional_fields()
            # turn ids to UIDs
            self._turn_ids_into_uids()
            data = self.data.copy()
        elif data['@type'].startswith('annex'):
            # reinject data from parent: config_id and in_name_of
            data['config_id'] = self.cfg.getId()
            if not data.get('in_name_of', None) and self.data.get('in_name_of', None):
                data['in_name_of'] = self.data['in_name_of']
            if data['@type'] == 'annex':
                # turn annex_type into content_category
                category_id = data['category_id']
                annex_type = self.cfg.annexes_types.item_annexes.get(category_id)
                annex_type_value = calculate_category_id(annex_type)
                data['content_category'] = annex_type_value
        return data

    def clean_data(self):
        """Remove parameters that are not attributes."""
        cleaned_data = self.data.copy()
        cleaned_data.pop('config_id', None)
        cleaned_data.pop('in_name_of', None)
        cleaned_data.pop('wf_transitions', None)
        return cleaned_data

    def _after_reply_hook(self, serialized_obj):
        """ """
        obj = self.context.get(serialized_obj['id'])
        # add a record to the item workflow_history to specify that item was created thru SOAP WS
        action_name = 'create_element_using_ws_rest'
        action_label = action_name + '_comments'
        add_wf_history_action(obj,
                              action_name=action_name,
                              action_label=action_label)

    def _check_unknown_data(self, serialized_obj):
        diff = set(self.cleaned_data.keys()).difference(serialized_obj.keys())
        if diff:
            unkown_msg = "Following field names were ignored : %s" % ', '.join(diff)
            self.warnings.append(unkown_msg)


class ItemPost(BasePost):

    @property
    def _turn_ids_into_uids_fieldnames(self):
        return ['proposingGroup', 'groupsInCharge', 'associatedGroups', 'optionalAdvisers']

    @property
    def _optional_fields(self):
        return self.cfg.listUsedItemAttributes()

    @property
    def _active_fields(self):
        return self.cfg.getUsedItemAttributes()

    def _wf_transition_additional_warning(self, tr):
        warning_message = ''
        if tr == 'present':
            warning_message = " Make sure a meeting accepting items " \
                "exists in configuration '{0}'!".format(self.cfg.getId())
        return warning_message


class MeetingPost(BasePost):

    @property
    def _optional_fields(self):
        return self.cfg.listUsedMeetingAttributes()

    @property
    def _active_fields(self):
        return self.cfg.getUsedMeetingAttributes()
