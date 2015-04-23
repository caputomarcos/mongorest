# -*- encoding: UTF-8 -*-

from logging import getLogger, CRITICAL

from pymongo.database import Database
from werkzeug.test import Client

from mongorest.testcase import TestCase


class TestTestCase(TestCase):

    def setUp(self):
        self.test_case = TestCase(methodName='__call__')

    def test_testcase_has_instance_of_pymongos_database(self):
        self.assertIsInstance(self.test_case.db, Database)

    def test_testcase_has_instance_of_werkzeugs_test_client(self):
        self.assertIsInstance(self.test_case.client, Client)

    def test_testcase_disables_all_logging(self):
        self.assertFalse(getLogger().isEnabledFor(CRITICAL))

    def test_testcase_cleans_the_database_after_running_a_test(self):
        class TestCleanDB(TestCase):
            def test_1(self):
                self.assertEqual(self.db.test.count(), 0)
                self.db.test.insert_one({})
                self.assertEqual(self.db.test.count(), 1)

        test = TestCleanDB(methodName='test_1')

        self.assertTrue(test().wasSuccessful())
        self.assertEqual(test.db.test.count(), 0)

