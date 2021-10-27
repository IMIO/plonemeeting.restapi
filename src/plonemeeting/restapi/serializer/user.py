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
        self.tool = api.portal.get_tool("portal_plonemeeting")
        # call _after__call__ that manages additional_values and extra_includes
        result = self._after__call__(result)
        return result

    def _configs_for_user(self):
        """ """
        cfgs = getattr(self, "cfgs", [])
        if not cfgs:
            with api.env.adopt_user(username=self.context.id):
                self.cfgs = self.tool.getActiveConfigs()
                cfgs = self.cfgs
        return cfgs

    def _available_extra_includes(self, result):
        """ """
        result["@extra_includes"] = [
            "groups", "app_groups", "configs", "categories", "classifiers"]
        return result

    def _extra_include(self, result):
        extra_include = listify(self.request.form.get("extra_include", []))

        if "groups" in extra_include:
            suffixes = self._get_param("suffixes", default=[], extra_include_name="groups")
            orgs = self.tool.get_orgs_for_user(
                user_id=self.context.id, suffixes=suffixes)
            result["extra_include_groups"] = []
            for org in orgs:
                serializer = self._get_serializer(org, "groups")
                result["extra_include_groups"].append(serializer())
            result["extra_include_groups_items_total"] = len(orgs)

        if "app_groups" in extra_include:
            groups = self.tool.get_plone_groups_for_user(
                userId=self.context.id, the_objects=True)
            result["extra_include_app_groups"] = [
                {"token": group.id,
                 "title": safe_unicode(group.getProperty("title"))}
                for group in groups]

        if "configs" in extra_include:
            result["extra_include_configs"] = []
            cfgs = self._configs_for_user()
            for cfg in cfgs:
                serializer = self._get_serializer(cfg, "configs")
                result["extra_include_configs"].append(serializer())
            result["extra_include_configs_items_total"] = len(cfgs)

        if "categories" in extra_include:
            result["extra_include_categories"] = {}
            cfgs = self._configs_for_user()
            config_ids = self._get_param("configs", default=[], extra_include_name="categories")
            for cfg in cfgs:
                cfg_id = cfg.getId()
                if config_ids and cfg_id not in config_ids:
                    continue
                result["extra_include_categories"][cfg_id] = []
                categories = cfg.getCategories(userId=self.context.id)
                for category in categories:
                    serializer = self._get_serializer(category, "categories")
                    result["extra_include_categories"][cfg_id].append(serializer())

        if "classifiers" in extra_include:
            result["extra_include_classifiers"] = {}
            cfgs = self._configs_for_user()
            config_ids = self._get_param("configs", default=[], extra_include_name="classifiers")
            for cfg in cfgs:
                cfg_id = cfg.getId()
                if config_ids and cfg_id not in config_ids:
                    continue
                result["extra_include_classifiers"][cfg_id] = []
                classifiers = cfg.getCategories(catType='classifiers', userId=self.context.id)
                for classifier in classifiers:
                    serializer = self._get_serializer(classifier, "classifiers")
                    result["extra_include_classifiers"][cfg_id].append(serializer())

        return result


@implementer(ISerializeToJson)
@adapter(IMemberData, IPMRestapiLayer)
class SerializeUserToJson(PMBaseUserSerializer):
    pass


@implementer(ISerializeToJsonSummary)
@adapter(IMemberData, IPMRestapiLayer)
class SerializeUserToJsonSummary(PMBaseUserSerializer):
    pass
