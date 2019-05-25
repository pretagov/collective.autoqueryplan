# -*- coding: utf-8 -*-
import Queue
import transaction
import unittest2 as unittest
from zope.component import getUtility
from zope.testing.loggingsupport import InstalledHandler

from collective.autoqueryplan.interfaces import Iautoqueryplan
from collective.autoqueryplan.testing import runAsyncTest
from collective.autoqueryplan.testing import TASK_QUEUE_FUNCTIONAL_TESTING
from collective.autoqueryplan import autoqueryplan


class TestLocalVolatileautoqueryplan(unittest.TestCase):

    layer = TASK_QUEUE_FUNCTIONAL_TESTING
    queue = 'test-queue'

    @property
    def task_queue(self):
        return getUtility(Iautoqueryplan, name=self.queue)

    def setUp(self):
        self.task_queue.queue = Queue.Queue()

    def testEmptyQueue(self):
        self.assertEqual(len(self.task_queue), 0)

    def testAddToQueue(self):
        autoqueryplan.add("/", queue=self.queue)
        self.assertEqual(len(self.task_queue), 0)

    def testCommitToQueue(self):
        autoqueryplan.add("/", queue=self.queue)
        self.assertEqual(len(self.task_queue), 0)
        transaction.commit()
        self.assertEqual(len(self.task_queue), 1)
        autoqueryplan.add("/Plone", queue=self.queue)
        self.assertEqual(len(self.task_queue), 1)
        transaction.commit()
        self.assertEqual(len(self.task_queue), 2)

    def _testConsumeFromQueue(self):
        self.assertEqual(len(self.task_queue), 0)

    def testConsumeFromQueue(self):
        self.assertEqual(len(self.task_queue), 0)
        autoqueryplan.add("/", queue=self.queue)
        autoqueryplan.add("/Plone", queue=self.queue)
        transaction.commit()
        self.assertEqual(len(self.task_queue), 2)

        handler = InstalledHandler("collective.autoqueryplan")
        runAsyncTest(self._testConsumeFromQueue)
        messages = [record.getMessage() for record in handler.records]
        self.assertEqual(messages[-2:],
                         ["http://nohost:/", "http://nohost:/Plone"])

    def testConsume100FromQueue(self):
        self.assertEqual(len(self.task_queue), 0)
        expected_result = []
        for i in range(100):
            autoqueryplan.add("/{0:02d}".format(i), queue=self.queue)
            expected_result.append("http://nohost:/{0:02d}".format(i))
        transaction.commit()
        self.assertEqual(len(self.task_queue), 100)

        handler = InstalledHandler("collective.autoqueryplan")
        runAsyncTest(self._testConsumeFromQueue)
        messages = [record.getMessage() for record in handler.records]

        self.assertEqual(sorted(messages[-100:]), expected_result)
