# -*- coding: utf-8 -*-

from imio.helpers.content import get_vocab
from imio.helpers.content import uuidsToCatalogBrains
from imio.helpers.content import uuidsToObjects
from imio.restapi.utils import listify
from plone.restapi.interfaces import ISerializeToJson
from plone.restapi.interfaces import ISerializeToJsonSummary
from plonemeeting.restapi.serializer.base import BaseATSerializeToJson
from plonemeeting.restapi.serializer.summary import PMBrainJSONSummarySerializer
from Products.PloneMeeting.interfaces import IMeetingConfig
from zope.component import adapter
from zope.component import queryMultiAdapter
from zope.interface import implementer
from zope.interface import Interface


class SerializeConfigToJsonBase(object):
    """ """
    def _extra_include(self, result):
        """ """
        extra_include = listify(self.request.form.get("extra_include", []))
        interface = ISerializeToJsonSummary
        if self.extra_include_fullobjects:
            interface = ISerializeToJson

        if "categories" in extra_include:
            categories = self.context.getCategories(onlySelectable=False)
            result["extra_include_categories"] = []
            for category in categories:
                serializer = queryMultiAdapter(
                    (category, self.request), interface)
                # manage expandable_elements for extra_includes
                serializer.extra_include_expandable_elements = \
                    self.extra_include_expandable_elements
                result["extra_include_categories"].append(serializer())
            result["extra_include_categories_items_total"] = len(categories)

        if "classifiers" in extra_include:
            classifiers = self.context.getCategories(catType='classifiers', onlySelectable=False)
            result["extra_include_classifiers"] = []
            for classifier in classifiers:
                serializer = queryMultiAdapter(
                    (classifier, self.request), interface)
                # manage expandable_elements for extra_includes
                serializer.extra_include_expandable_elements = \
                    self.extra_include_expandable_elements
                result["extra_include_classifiers"].append(serializer())
            result["extra_include_classifiers_items_total"] = len(classifiers)

        if "pod_templates" in extra_include:
            pod_templates = [obj for obj in self.context.podtemplates.objectValues()
                             if getattr(obj, 'enabled', False)]
            result["extra_include_pod_templates"] = []
            for pod_template in pod_templates:
                serializer = queryMultiAdapter(
                    (pod_template, self.request), interface)
                # manage expandable_elements for extra_includes
                serializer.extra_include_expandable_elements = \
                    self.extra_include_expandable_elements
                result["extra_include_pod_templates"].append(serializer())
            result["extra_include_pod_templates_items_total"] = len(pod_templates)

        if "searches" in extra_include:
            collections = [obj for obj in self.context.searches.searches_items.objectValues()
                           if (obj.portal_type == 'DashboardCollection' and obj.enabled)]
            result["extra_include_searches"] = []
            for collection in collections:
                serializer = queryMultiAdapter(
                    (collection, self.request), interface)
                # manage expandable_elements for extra_includes
                serializer.extra_include_expandable_elements = \
                    self.extra_include_expandable_elements
                result["extra_include_searches"].append(serializer())
            result["extra_include_searches_items_total"] = len(collections)

        if "proposing_groups" in extra_include:
            orgs = self.context.getUsingGroups(theObjects=True)
            result["extra_include_proposing_groups"] = []
            for org in orgs:
                serializer = queryMultiAdapter(
                    (org, self.request), interface)
                # manage expandable_elements for extra_includes
                serializer.extra_include_expandable_elements = \
                    self.extra_include_expandable_elements
                result["extra_include_proposing_groups"].append(serializer())
            result["extra_include_proposing_groups_items_total"] = len(orgs)

        if "associated_groups" in extra_include:
            vocab = get_vocab(
                self.context,
                'Products.PloneMeeting.vocabularies.associatedgroupsvocabulary')
            org_uids = [term.value for term in vocab._terms]
            if self.extra_include_fullobjects:
                orgs = uuidsToObjects(org_uids, ordered=True)
            else:
                orgs = uuidsToCatalogBrains(org_uids, ordered=True)
            result["extra_include_associated_groups"] = []
            for org in orgs:
                serializer = queryMultiAdapter(
                    (org, self.request), interface)
                # manage expandable_elements for extra_includes
                serializer.extra_include_expandable_elements = \
                    self.extra_include_expandable_elements
                result["extra_include_associated_groups"].append(serializer())
            result["extra_include_associated_groups_items_total"] = len(orgs)

        if "groups_in_charge" in extra_include:
            vocab = get_vocab(
                self.context,
                'Products.PloneMeeting.vocabularies.groupsinchargevocabulary')
            org_uids = [term.value for term in vocab._terms]
            if self.extra_include_fullobjects:
                orgs = uuidsToObjects(org_uids, ordered=True)
            else:
                orgs = uuidsToCatalogBrains(org_uids, ordered=True)
            result["extra_include_groups_in_charge"] = []
            for org in orgs:
                serializer = queryMultiAdapter(
                    (org, self.request), interface)
                # manage expandable_elements for extra_includes
                serializer.extra_include_expandable_elements = \
                    self.extra_include_expandable_elements
                result["extra_include_groups_in_charge"].append(serializer())
            result["extra_include_groups_in_charge_items_total"] = len(orgs)

        return result


@implementer(ISerializeToJson)
@adapter(IMeetingConfig, Interface)
class SerializeToJson(SerializeConfigToJsonBase, BaseATSerializeToJson):
    """ """


@implementer(ISerializeToJsonSummary)
@adapter(IMeetingConfig, Interface)
class SerializeToJsonSummary(SerializeConfigToJsonBase, PMBrainJSONSummarySerializer):
    """ """
