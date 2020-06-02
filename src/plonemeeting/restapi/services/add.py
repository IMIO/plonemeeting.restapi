# -*- coding: utf-8 -*-

from AccessControl import Unauthorized
from Products.PloneMeeting.utils import add_wf_history_action
from imio.restapi.services.add import FolderPost
from plone import api
from plone.restapi.deserializer import json_body
from Products.PloneMeeting.utils import org_id_to_uid
from zExceptions import BadRequest

import json


class PMFolderPost(FolderPost):

    def __init__(self, context, request):
        super(PMFolderPost, self).__init__(context, request)
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

    def __call__(self):
        in_name_of = self.data.get('in_name_of')
        self.prepare_data()
        self.clean_data()

        # set new BODY when cleaned data
        self.request['BODY'] = json.dumps(self.data)

        # change context, the view is called on portal, when need
        # the set context to place where element will be added
        self.context = self.tool.getPloneMeetingFolder(self.cfg.getId(), userId=in_name_of)
        if in_name_of and self._may_in_name_of():
            with api.env.adopt_user(username=in_name_of):
                return super(PMFolderPost, self).__call__()
        else:
            return super(PMFolderPost, self).__call__()

    def _may_in_name_of(self):
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
        if 'type' not in self.data or 'type' == 'item':
            self.data['@type'] = self.cfg.getItemTypeName()
        elif 'type' == 'meeting':
            self.data['@type'] = self.cfg.getMeetingTypeName()
        return self.data.get('@type')

    @property
    def _data(self):
        return json_body(self.request)

    @property
    def _turn_ids_into_uids_fieldnames(self):
        return ['proposingGroup', 'groupsInCharge', 'associatedGroups', 'optionalAdvisers']

    def _turn_ids_into_uids(self):
        for field_name in self._turn_ids_into_uids_fieldnames:
            field_value = self.data.get(field_name)
            if field_value:
                if hasattr(field_value, '__iter__'):
                    self.data[field_name] = [org_id_to_uid(org_id, raise_on_error=False) or org_id
                                             for org_id in field_value if org_id]
                else:
                    self.data[field_name] = org_id_to_uid(field_value, raise_on_error=False)

    def _check_optional_fields(self):
        optional_fields = self.cfg.listUsedItemAttributes()
        active_fields = self.cfg.getUsedItemAttributes()
        for field_name, field_value in self.data.items():
            # if the field is an optional field that is not used
            # and that has a value (contains data), we raise
            if field_name in optional_fields and \
               field_name not in active_fields and \
               field_value:
                raise BadRequest("The optional field \"%s\" is not activated in this configuration!"
                                 % field_name)

    def _check_unknown_data(self, serialized_obj):
        diff = set(self.data.keys()).difference(serialized_obj.keys())
        if diff:
            unkown_msg = "Following field names were ignored : %s" % ', '.join(diff)
            self.warnings.append(unkown_msg)

    def prepare_data(self):
        # check that given values are useable, will raise if not
        self._check_optional_fields()
        # turn ids to UIDs
        self._turn_ids_into_uids()

    def clean_data(self):
        """Remove parameters that are not attributes."""
        self.data.pop('type', None)
        self.data.pop('config_id', None)
        self.data.pop('in_name_of', None)

    def add_history_entry(self, obj):
        # add a record to the item workflow_history to specify that item was created thru SOAP WS
        action_name = 'create_element_using_ws_rest'
        action_label = action_name + '_comments'
        add_wf_history_action(obj,
                              action_name=action_name,
                              action_label=action_label)

    def reply(self):
        serialized_obj = super(PMFolderPost, self).reply()
        self._check_unknown_data(serialized_obj)
        serialized_obj['@warnings'] = self.warnings
        self.add_history_entry(self.context.get(serialized_obj['id']))
        return serialized_obj
