# -*- coding: utf-8 -*-

from plonemeeting.restapi.tests.base import BaseTestCase

import transaction


class testSerializerItem(BaseTestCase):
    """ """

    def test_restapi_item_serializer(self):
        """ISerializeToJson"""
        pass

    def test_restapi_item_summary(self):
        """ISerializeToJsonSummary"""
        pass


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    # add a prefix to avoid every PM tests to be executed
    suite.addTest(makeSuite(testSerializerItem, prefix='test_restapi_'))
    return suite
