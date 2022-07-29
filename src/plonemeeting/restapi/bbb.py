# -*- coding: utf-8 -*-

from plone import api


# this package holds methods legacy to support PloneMeeting 4.1.x and 4.2.x
# this needs to be removed will dropping support for PloneMeeting 4.1.x


def get_filtered_plone_groups_for_user(org_uids=[], userId=None, suffixes=[], the_objects=False):
    """Copy from ToolPloneMeeting.get_filtered_plone_groups_for_user."""

    tool = api.portal.get_tool('portal_plonemeeting')
    user_groups = tool.get_plone_groups_for_user(
        userId=userId, the_objects=the_objects)
    if the_objects:
        user_groups = [plone_group for plone_group in user_groups
                       if (not org_uids or plone_group.id.split('_')[0] in org_uids) and
                       (not suffixes or '_' in plone_group.id and plone_group.id.split('_')[1] in suffixes)]
    else:
        user_groups = [plone_group_id for plone_group_id in user_groups
                       if (not org_uids or plone_group_id.split('_')[0] in org_uids) and
                       (not suffixes or '_' in plone_group_id and plone_group_id.split('_')[1] in suffixes)]
    return sorted(user_groups)


def getActiveConfigs(check_using_groups=True, check_access=True):
    '''Copy from ToolPloneMeeting.getActiveConfigs.'''
    tool = api.portal.get_tool('portal_plonemeeting')
    res = []
    for cfg in tool.objectValues('MeetingConfig'):
        if api.content.get_state(cfg) == 'active' and \
           (not check_access or
            (tool.checkMayView(cfg) and
                (tool.isManager(cfg) or tool.isPowerObserverForCfg(cfg) or
                    (check_using_groups and tool.get_orgs_for_user(
                        using_groups=cfg.getUsingGroups()))))):
            res.append(cfg)
    return res
