import logging

from unittest import TestCase
from testfixtures import log_capture

from translators import google


class TseLoggerTest(TestCase):
    @log_capture()
    def test_on_logging(self, capture):
        google('Test massage', 'en', 'ru')

        self.assertEqual(capture.actual()[3][0], 'TSE LOGGER')
        self.assertEqual(capture.actual()[3][1], 'INFO')
        self.assertEqual(capture.actual()[3][2][:len('UseTimeSeconds(fn: google_api):')],
                         'UseTimeSeconds(fn: google_api):')

    @log_capture()
    def test_logging_level_error(self, capture):
        logger = logging.getLogger('TSE LOGGER')
        logger.setLevel('ERROR')
        google('Test massage', 'en', 'ru')
        for log in capture.actual():
            self.assertNotEqual(log[0] + ' ' + log[1], 'TSE LOGGER ERROR')
        logger.setLevel('INFO')
