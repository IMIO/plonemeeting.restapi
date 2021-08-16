# -*- coding: utf-8 -*-

from plone.restapi.deserializer import boolean_value
from plone.restapi.interfaces import ISerializeToJson
from plone.restapi.interfaces import ISerializeToJsonSummary
from AccessControl import Unauthorized
from plone import api
from plonemeeting.restapi.config import IN_NAME_OF_UNAUTHORIZED
from zExceptions import BadRequest
from zope.globalrequest import getRequest
from zope.component import queryMultiAdapter

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


def get_serializer(obj, extra_include_name=None, serializer=None):
    """ """
    request = getRequest()
    interface = ISerializeToJsonSummary
    if get_param("fullobjects", extra_include_name=extra_include_name, serializer=serializer):
        interface = ISerializeToJson
    serializer = queryMultiAdapter((obj, request), interface)
    if extra_include_name:
        serializer._extra_include_name = extra_include_name
    return serializer


def get_param(value, default=False, extra_include_name=None, serializer=None):
    """If current serialized element is an extra_include,
       infos in request.form are relative to extra_include,
       else information are directly available.
       For extra_include, a parameter is passed like :
       ?extra_include=extra_include_name:parameter_name:value so
       ?extra_include_category_include_all=false."""
    request = getRequest()
    # extra_include_name is stored on serializer or passed as parameter when serializer
    # still not initialized, this is the case for parameter "fullobjects" as from this
    # will depend the interface to use to get the serializer
    extra_include_name = serializer and \
        getattr(serializer, "_extra_include_name", extra_include_name)
    if extra_include_name:
        # change param value
        value = "extra_include_{0}_{1}".format(extra_include_name, value)

    param = request.form.get(value, None)

    # param was not found in request.form
    if param is None:
        param = default
    elif default in (True, False):
        param = boolean_value(param)
    return param
