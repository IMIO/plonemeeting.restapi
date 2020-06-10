# -*- coding: utf-8 -*-

from AccessControl import Unauthorized
from plonemeeting.restapi.config import IN_NAME_OF_UNAUTHORIZED


def check_in_name_of(instance, data):
    """ """
    in_name_of = data.get('in_name_of', None)
    if in_name_of:
        if not bool(instance.tool.isManager(instance.cfg)):
            raise Unauthorized(IN_NAME_OF_UNAUTHORIZED % in_name_of)
    return in_name_of


def listify(value):
    ''' '''
    if not hasattr(value, '__iter__'):
        value = [value]
    return value
