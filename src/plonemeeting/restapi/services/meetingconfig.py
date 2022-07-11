# -*- coding: utf-8 -*-

from plonemeeting.restapi.services.search import PMSearchGet


class ConfigSearchGet(PMSearchGet):
    """Returns a serialized content object.
    """

    @property
    def _type(self):
        # forced to "config"
        return "config"

    def reply(self):
        res = self._process_reply()
        if res["items"] and hasattr(self, "cfg"):
            # we asked for one single MeetingConfig, return it (not a list of result)
            res = res["items"][0]
        return res
