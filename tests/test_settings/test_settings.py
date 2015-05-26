# -*- encoding: UTF-8 -*-
from __future__ import absolute_import, unicode_literals

from os import environ

from mongorest.settings import settings
from mongorest.testcase import TestCase


class TestSettings(TestCase):

    def test_settings_has_default_values_for_database(self):
        environ.pop('MONGOREST_SETTINGS_MODULE', None)

        self.assertIsNotNone(settings.MONGODB)
        self.assertEqual(settings.MONGODB['URI'], '')
        self.assertEqual(settings.MONGODB['USERNAME'], '')
        self.assertEqual(settings.MONGODB['PASSWORD'], '')
        self.assertEqual(settings.MONGODB['HOST'], 'localhost')
        self.assertEqual(settings.MONGODB['HOSTS'], [])
        self.assertEqual(settings.MONGODB['PORT'], 27017)
        self.assertEqual(settings.MONGODB['PORTS'], [])
        self.assertEqual(settings.MONGODB['DATABASE'], 'mongorest')
        self.assertEqual(settings.MONGODB['OPTIONS'], [])

    def test_a_default_setting_can_be_overwritten(self):
        environ.pop('MONGOREST_SETTINGS_MODULE', None)

        self.assertEqual(settings.MONGODB['URI'], '')

        environ['MONGOREST_SETTINGS_MODULE'] = 'tests.test_settings.fixtures.settings'

        self.assertEqual(settings.MONGODB['URI'], 'test')

    def test_a_new_setting_value_can_be_added(self):
        environ.pop('MONGOREST_SETTINGS_MODULE', None)

        with self.assertRaises(AttributeError):
            settings.TEST

        environ['MONGOREST_SETTINGS_MODULE'] = 'tests.test_settings.fixtures.settings'

        self.assertEqual(settings.TEST, 'test')

    def test_an_invalid_setting_will_raise_error(self):
        environ.pop('MONGOREST_SETTINGS_MODULE', None)

        with self.assertRaises(AttributeError):
            settings.i_am_an_invalid_setting