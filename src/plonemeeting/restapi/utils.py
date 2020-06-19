# -*- coding: utf-8 -*-

from AccessControl import Unauthorized
from plone import api
from plonemeeting.restapi.config import IN_NAME_OF_UNAUTHORIZED
from zExceptions import BadRequest

IN_NAME_OF_USER_NOT_FOUND = 'The in_name_of user "%s" was not found!'


def check_in_name_of(instance, data):
    """ """
    in_name_of = data.get("in_name_of", None)
    if in_name_of:
        if not bool(instance.tool.isManager(instance.cfg)):
            raise Unauthorized(IN_NAME_OF_UNAUTHORIZED % in_name_of)
        user = api.user.get(in_name_of)
        if not user:
            raise BadRequest(IN_NAME_OF_USER_NOT_FOUND % in_name_of)
    return in_name_of
