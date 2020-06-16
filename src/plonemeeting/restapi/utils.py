# -*- coding: utf-8 -*-

from AccessControl import Unauthorized
from plone import api
from plonemeeting.restapi.config import IN_NAME_OF_UNAUTHORIZED
from zExceptions import BadRequest

IN_NAME_OF_USER_NOT_FOUND = "The in_name_of user \"%s\" was not found!"


def check_in_name_of(instance, data):
    """ """
    in_name_of = data.get('in_name_of', None)
    if in_name_of:
        if not bool(instance.tool.isManager(instance.cfg)):
            raise Unauthorized(IN_NAME_OF_UNAUTHORIZED % in_name_of)
        user = api.user.get(in_name_of)
        if not user:
            raise BadRequest(IN_NAME_OF_USER_NOT_FOUND % in_name_of)
    return in_name_of


def listify(value):
    ''' '''
    if not hasattr(value, '__iter__'):
        value = [value]
    return value


def sizeof_fmt(num, suffix='o'):
    """Readable file size
    :param num: Bytes value
    :type num: int
    :param suffix: Unit suffix (optionnal) default = o
    :type suffix: str
    :rtype: str
    """
    for unit in ['', 'k', 'M', 'G', 'T', 'P', 'E', 'Z']:
        if abs(num) < 1024.0:
            return "%3.1f %s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)
