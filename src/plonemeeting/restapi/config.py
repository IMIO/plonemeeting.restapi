# -*- coding: utf-8 -*-

CONFIG_ID_ERROR = 'The "config_id" parameter must be given!'
CONFIG_ID_TYPE_ERROR = 'A "config_id" can not be given when parameter "type" is "config"!'
CONFIG_ID_NOT_FOUND_ERROR = 'The given "config_id" named "%s" was not found!'
ANNEXES_FILTER_VALUES = [
    "to_print", "confidential", "publishable", "to_sign", "signed"]
INDEX_CORRESPONDENCES = {
    'getConfigId': 'config_id',
    'review_state': 'state',
    'portal_type': 'type',
    'UID': 'uid'}
