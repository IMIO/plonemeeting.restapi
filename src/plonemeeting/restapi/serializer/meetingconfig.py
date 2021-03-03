# -*- coding: utf-8 -*-

from imio.helpers.content import get_vocab
from imio.helpers.content import uuidsToObjects
from imio.restapi.utils import listify
from plone.restapi.interfaces import ISerializeToJson
from plonemeeting.restapi.serializer.base import BaseATSerializeToJson
from Products.PloneMeeting.interfaces import IMeetingConfig
from zope.component import adapter
from zope.component import queryMultiAdapter
from zope.interface import implementer
from zope.interface import Interface


@implementer(ISerializeToJson)
@adapter(IMeetingConfig, Interface)
class SerializeToJson(BaseATSerializeToJson):
    """ """

    def __call__(self, version=None, include_items=False):
        """Change include_items=False by default."""
        result = super(SerializeToJson, self).__call__(
            version=version, include_items=include_items
        )
        return result

    def _extra_include(self, result):
        """ """
        extra_include = listify(self.request.form.get("extra_include", []))
        if "categories" in extra_include:
            categories = self.context.getCategories(onlySelectable=False)
            result["extra_include_categories"] = []
            for category in categories:
                serializer = queryMultiAdapter(
                    (category, self.request), ISerializeToJson
                )
                result["extra_include_categories"].append(serializer())

        if "classifiers" in extra_include:
            classifiers = self.context.getCategories(catType='classifiers', onlySelectable=False)
            result["extra_include_classifiers"] = []
            for classifier in classifiers:
                serializer = queryMultiAdapter(
                    (classifier, self.request), ISerializeToJson
                )
                result["extra_include_classifiers"].append(serializer())

        if "pod_templates" in extra_include:
            pod_templates = [obj for obj in self.context.podtemplates.objectValues()
                             if getattr(obj, 'enabled', False)]
            result["extra_include_pod_templates"] = []
            for pod_template in pod_templates:
                serializer = queryMultiAdapter(
                    (pod_template, self.request), ISerializeToJson
                )
                result["extra_include_pod_templates"].append(serializer())

        if "searches" in extra_include:
            collections = [obj for obj in self.context.searches.searches_items.objectValues()
                           if (obj.portal_type == 'DashboardCollection' and obj.enabled)]
            result["extra_include_searches"] = []
            for collection in collections:
                serializer = queryMultiAdapter(
                    (collection, self.request), ISerializeToJson
                )
                result["extra_include_searches"].append(serializer(include_items=False))

        if "proposing_groups" in extra_include:
            orgs = self.context.getUsingGroups(theObjects=True)
            result["extra_include_proposing_groups"] = []
            for org in orgs:
                serializer = queryMultiAdapter(
                    (org, self.request), ISerializeToJson
                )
                result["extra_include_proposing_groups"].append(serializer(include_items=False))

        if "associated_groups" in extra_include:
            vocab = get_vocab(
                self.context,
                'Products.PloneMeeting.vocabularies.associatedgroupsvocabulary')
            org_uids = [term.value for term in vocab._terms]
            orgs = uuidsToObjects(org_uids, ordered=True)
            result["extra_include_associated_groups"] = []
            for org in orgs:
                serializer = queryMultiAdapter(
                    (org, self.request), ISerializeToJson
                )
                result["extra_include_associated_groups"].append(serializer(include_items=False))

        if "groups_in_charge" in extra_include:
            vocab = get_vocab(
                self.context,
                'Products.PloneMeeting.vocabularies.groupsinchargevocabulary')
            org_uids = [term.value for term in vocab._terms]
            orgs = uuidsToObjects(org_uids, ordered=True)
            result["extra_include_groups_in_charge"] = []
            for org in orgs:
                serializer = queryMultiAdapter(
                    (org, self.request), ISerializeToJson
                )
                result["extra_include_groups_in_charge"].append(serializer(include_items=False))

        return result
