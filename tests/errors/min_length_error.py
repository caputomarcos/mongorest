# -*- encoding: UTF-8 -*-
from __future__ import absolute_import, unicode_literals

from mongorest.errors import MinLengthError
from mongorest.testcase import TestCase


class TestMinLengthError(TestCase):

    def test_min_length_error_sets_correct_fields(self):
        self.assertEqual(
            MinLengthError('collection', 'field', 'min_length'),
            {
                'error_code': 27,
                'error_type': 'MinLengthError',
                'error_message': 'Minimum length for field \'field\' on '
                                 'collection \'collection\' is min_length.',
                'collection': 'collection',
                'field': 'field',
                'min_length': 'min_length'
            }
        )
