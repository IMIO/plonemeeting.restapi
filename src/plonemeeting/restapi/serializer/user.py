# -*- coding: utf-8 -*-

from imio.restapi.utils import listify
from plone import api
from plone.restapi.interfaces import ISerializeToJson
from plone.restapi.interfaces import ISerializeToJsonSummary
from plone.restapi.serializer.user import BaseSerializer as BaseUserSerializer
from plonemeeting.restapi.interfaces import IPMRestapiLayer
from plonemeeting.restapi.serializer.base import BaseSerializeToJson
from Products.CMFCore.interfaces._tools import IMemberData
from Products.CMFPlone.utils import safe_unicode
from zope.component import adapter
from zope.interface import implementer


class PMBaseUserSerializer(BaseUserSerializer, BaseSerializeToJson):

    def __call__(self):
        result = super(PMBaseUserSerializer, self).__call__()
        # call _after__call__ that manages additional_values and extra_includes
        result = self._after__call__(result)
        return result

    def _extra_include(self, result):
        extra_include = listify(self.request.form.get("extra_include", []))
        tool = api.portal.get_tool("portal_plonemeeting")

        if "groups" in extra_include:
            suffixes = self._get_param("suffixes", default=[], extra_include_name="groups")
            orgs = tool.get_orgs_for_user(user_id=self.context.id, suffixes=suffixes)
            result["extra_include_groups"] = []
            for org in orgs:
                serializer = self._get_serializer(org, "groups")
                result["extra_include_groups"].append(serializer())
            result["extra_include_groups_items_total"] = len(orgs)

        if "app_groups" in extra_include:
            groups = tool.get_plone_groups_for_user(userId=self.context.id, the_objects=True)
            result["extra_include_app_groups"] = [
                {"token": group.id,
                 "title": safe_unicode(group.getProperty("title"))}
                for group in groups]

        if "configs" in extra_include:
            with api.env.adopt_user(username=self.context.id):
                cfgs = tool.getActiveConfigs()
                result["extra_include_configs"] = []
                for cfg in cfgs:
                    serializer = self._get_serializer(cfg, "configs")
                    result["extra_include_configs"].append(serializer())
                result["extra_include_configs_items_total"] = len(cfgs)

        return result


@implementer(ISerializeToJson)
@adapter(IMemberData, IPMRestapiLayer)
class SerializeUserToJson(PMBaseUserSerializer):
    pass


@implementer(ISerializeToJsonSummary)
@adapter(IMemberData, IPMRestapiLayer)
class SerializeUserToJsonSummary(PMBaseUserSerializer):
    pass
