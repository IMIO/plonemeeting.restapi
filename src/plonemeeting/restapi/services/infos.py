# -*- coding: utf-8 -*-

from AccessControl import Unauthorized
from imio.pyutils.system import read_dir
from imio.pyutils.system import read_file
from plone import api
from plone.restapi.services import Service
from plonemeeting.restapi.utils import listify
from plonemeeting.restapi.utils import sizeof_fmt
from Products.CPUtils.Extensions.utils import tobytes

import os

STATS_UNAUTHORIZED = "User must be Manager to use the \"stats\" option!"


class InfosGet(Service):
    """Returns informations about installed versions."""

    def _stats_users(self):
        portal_membership = api.portal.get_tool('portal_membership')
        users = portal_membership.searchForMembers()
        count = 0
        for user in users:
            user_groups = user.getGroups()
            if user_groups and user_groups != ['AuthenticatedUsers']:
                count = count + 1
        return count

    def _stats_groups(self):
        return len(api.group.get_groups())

    def _stats_types(self):
        types = {}
        tool = api.portal.get_tool('portal_plonemeeting')
        catalog = api.portal.get_tool('portal_catalog')
        # types MeetingConfig
        mConfigs = tool.getActiveConfigs(check_using_groups=False)
        types['MeetingConfig'] = len(mConfigs)
        meeting_types = [cfg.getMeetingTypeName() for cfg in mConfigs]
        # types Meeting
        types['Meeting'] = len(catalog(portal_type=meeting_types))
        item_types = [cfg.getItemTypeName() for cfg in mConfigs]
        # types MeetingItem
        types['MeetingItem'] = len(catalog(portal_type=item_types))
        # types annex
        types['annex'] = len(catalog(portal_type='annex'))
        # types annexDecision
        types['annexDecision'] = len(catalog(portal_type='annexDecision'))
        # types advices (meetingadvice, meetingadvicefinances, ...)
        for advice_type in tool.getAdvicePortalTypes(as_ids=True):
            types[advice_type] = len(catalog(portal_type=advice_type))
        return types

    def _stats_database(self):
        # zope
        database = {'fs_sz': 0, 'bl_sz': 0}
        app = self.context.restrictedTraverse('/')
        dbs = app['Control_Panel']['Database']
        for db in dbs.getDatabaseNames():
            readable_size = dbs[db].db_size()
            size = int(tobytes(readable_size[:-1] + ' ' + readable_size[-1:] + 'B'))
            # keep only largest
            if size > database['fs_sz']:
                database['fs_sz'] = size
                database['fs_sz_readable'] = sizeof_fmt(size)
        # blobstorage
        instdir = os.getenv('PWD')
        vardir = os.path.join(instdir, 'var')
        for blobdirname in read_dir(vardir, only_folders=True):
            if not blobdirname.startswith('blobstorage'):
                continue
            sizefile = os.path.join(vardir, blobdirname, 'size.txt')
            if os.path.exists(sizefile):
                lines = read_file(sizefile)
                size = int(lines and lines[0] or 0)
                # keep only largest
                if size > database['bl_sz']:
                    database['bl_sz'] = size
                    database['bl_sz_readable'] = sizeof_fmt(size)
                    database['bl_nm'] = blobdirname
        return database

    def _extra_include(self, result):
        ''' '''
        extra_include = listify(self.request.form.get('extra_include', []))
        if 'stats' in extra_include:
            tool = api.portal.get_tool('portal_plonemeeting')
            if not tool.isManager(self.context, realManagers=True):
                raise Unauthorized(STATS_UNAUTHORIZED)

            # all this was gently borrowed from imio.updates inst_infos.py
            stats = {}
            stats['users'] = self._stats_users()
            stats['groups'] = self._stats_groups()
            stats['types'] = self._stats_types()
            stats['database'] = self._stats_database()
            result['stats'] = stats
        return result

    def reply(self):
        result = {}
        for package_name in ['Products.PloneMeeting', 'imio.restapi', 'plonemeeting.restapi']:
            version = api.env.get_distribution(package_name)._version
            result[package_name] = version
        user = api.user.get_current()
        result['connected_user'] = user.getId()
        result = self._extra_include(result)
        return result
