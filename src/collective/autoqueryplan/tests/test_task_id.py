# -*- coding: utf-8 -*-
import Queue
import logging
import unittest

from plone.testing import z2
import transaction
from zope.component import getUtility
from zope.testing.loggingsupport import InstalledHandler

from collective.autoqueryplan import autoqueryplan
from collective.autoqueryplan.interfaces import Iautoqueryplan
from collective.autoqueryplan.testing import (
    LocalautoqueryplanServerLayer,
    runAsyncTest
)


logger = logging.getLogger('collective.autoqueryplan')


class TaskIdLoggingautoqueryplanServerLayer(LocalautoqueryplanServerLayer):

    def setUp(self):
        super(TaskIdLoggingautoqueryplanServerLayer, self).setUp()

        def logging_handler(app, request, response):
            logger.info(request.getHeader("X-Task-Id"))
            response.stdout.write('HTTP/1.1 204\r\n')
            response.stdout.close()

        self['server'].handler = logging_handler


TASK_QUEUE_FIXTURE = TaskIdLoggingautoqueryplanServerLayer(queue='test-queue')

TASK_QUEUE_FUNCTIONAL_TESTING = z2.FunctionalTesting(
    bases=(TASK_QUEUE_FIXTURE,),
    name='autoqueryplan:Functional')


class TestLocalVolatileautoqueryplan(unittest.TestCase):

    layer = TASK_QUEUE_FUNCTIONAL_TESTING
    queue = 'test-queue'

    @property
    def task_queue(self):
        return getUtility(Iautoqueryplan, name=self.queue)

    def setUp(self):
        self.task_queue.queue = Queue.Queue()

    def _testConsumeFromQueue(self):
        self.assertEqual(len(self.task_queue), 0)

    def testTaskId(self):
        self.assertEqual(len(self.task_queue), 0)
        a = autoqueryplan.add("/", queue=self.queue)
        b = autoqueryplan.add("/Plone", queue=self.queue)
        transaction.commit()
        self.assertEqual(len(self.task_queue), 2)

        handler = InstalledHandler("collective.autoqueryplan")
        runAsyncTest(self._testConsumeFromQueue)
        messages = [record.getMessage() for record in handler.records]
        self.assertEqual(messages[-2:], [a, b])

