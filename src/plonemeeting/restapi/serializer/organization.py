# -*- coding: utf-8 -*-

from plone.restapi.interfaces import ISerializeToJson
from plone.restapi.interfaces import ISerializeToJsonSummary
from plonemeeting.restapi.serializer.base import BaseDXSerializeFolderToJson
from plonemeeting.restapi.serializer.summary import PMBrainJSONSummarySerializer
from Products.PloneMeeting.content.organization import IPMOrganization
from zope.component import adapter
from zope.interface import implementer
from zope.interface import Interface


def org_full_id(org):
    """Return "full_id" for given p_org organization."""
    return "/".join(
        [o.getId() for o
         in org.get_organizations_chain(first_index=1)])


class SerializeOrganizationToJsonBase(object):
    """ """


@implementer(ISerializeToJson)
@adapter(IPMOrganization, Interface)
class SerializeToJson(SerializeOrganizationToJsonBase, BaseDXSerializeFolderToJson):
    """ """

    def _include_custom(self, obj, result):
        """Include "full_id" by default."""
        result["full_id"] = org_full_id(obj)
        return result


@implementer(ISerializeToJsonSummary)
@adapter(IPMOrganization, Interface)
class SerializeToJsonSummary(SerializeOrganizationToJsonBase, PMBrainJSONSummarySerializer):
    """ """
