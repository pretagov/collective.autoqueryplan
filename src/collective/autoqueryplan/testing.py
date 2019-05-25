# -*- coding: utf-8 -*-
import asyncore
import logging
from App.config import getConfiguration

from zope.configuration import xmlconfig
from zope.component import getSiteManager

from plone.testing import Layer
from plone.testing import z2
from collective.autoqueryplan.config import HAS_REDIS
from collective.autoqueryplan.config import HAS_MSGPACK
from collective.autoqueryplan import autoqueryplan
from collective.autoqueryplan.interfaces import Iautoqueryplan

if HAS_REDIS and HAS_MSGPACK:
    from collective.autoqueryplan import redisqueue

logger = logging.getLogger('collective.autoqueryplan')

class autoqueryplanServerLayer(Layer):
    defaultBases = (z2.STARTUP,)

    def __init__(self, queue='test-queue', zserver_enabled=False):
        super(autoqueryplanServerLayer, self).__init__()
        self.queue = queue
        self.zserver_enabled = zserver_enabled

    def setUp(self):
        import collective.autoqueryplan
        xmlconfig.file('configure.zcml', collective.autoqueryplan,
                       context=self['configurationContext'])

        # Configure
        config = getConfiguration()
        config.product_config = {'collective.autoqueryplan': {'queue': self.queue}}
        autoqueryplan.reset()

        # Define logging request handler to replace ZPublisher
        def logging_handler(app, request, response):
            logger.info(request.getURL() + request.get("PATH_INFO"))
            response.stdout.write('HTTP/1.1 204\r\n')
            response.stdout.close()

        # Define ZPublisher-based request handler to be used with zserver
        def zserver_handler(app, request, response):
            from ZPublisher import publish_module
            publish_module(app, request=request, response=response)

        # Create autoqueryplanServer
        from collective.autoqueryplan.server import autoqueryplanServer
        if not self.zserver_enabled:
            self['server'] = autoqueryplanServer(queue=self.queue,
                                             handler=logging_handler)
        else:
            self['server'] = autoqueryplanServer(queue=self.queue,
                                             handler=zserver_handler,
                                             concurrent_limit=0)
            # concurrent_limit=0, because of limitations in z2.ZServer

    def tearDown(self):
        self['server'].handle_close(force=True)

    def testTearDown(self):
        autoqueryplan.reset()


class LocalautoqueryplanServerLayer(autoqueryplanServerLayer):

    def setUp(self):
        queue = autoqueryplan.LocalVolatileautoqueryplan()
        sm = getSiteManager()
        sm.registerUtility(queue, provided=Iautoqueryplan, name='test-queue')
        super(LocalautoqueryplanServerLayer, self).setUp()


TASK_QUEUE_FIXTURE = LocalautoqueryplanServerLayer(queue='test-queue')
TASK_QUEUE_ZSERVER_FIXTURE =\
    LocalautoqueryplanServerLayer(queue='test-queue', zserver_enabled=True)

TASK_QUEUE_INTEGRATION_TESTING = z2.IntegrationTesting(
    bases=(TASK_QUEUE_FIXTURE,),
    name='autoqueryplan:Integration')

TASK_QUEUE_FUNCTIONAL_TESTING = z2.FunctionalTesting(
    bases=(TASK_QUEUE_FIXTURE,),
    name='autoqueryplan:Functional')


class RedisautoqueryplanServerLayer(autoqueryplanServerLayer):

    def setUp(self):
        queue = redisqueue.Redisautoqueryplan()
        sm = getSiteManager()
        sm.registerUtility(queue, provided=Iautoqueryplan, name='test-queue')
        super(RedisautoqueryplanServerLayer, self).setUp()

REDIS_TASK_QUEUE_FIXTURE = RedisautoqueryplanServerLayer(queue='test-queue')
REDIS_TASK_QUEUE_ZSERVER_FIXTURE =\
    RedisautoqueryplanServerLayer(queue='test-queue', zserver_enabled=True)

REDIS_TASK_QUEUE_INTEGRATION_TESTING = z2.IntegrationTesting(
    bases=(REDIS_TASK_QUEUE_FIXTURE,),
    name='Redisautoqueryplan:Integration')

REDIS_TASK_QUEUE_FUNCTIONAL_TESTING = z2.FunctionalTesting(
    bases=(REDIS_TASK_QUEUE_FIXTURE,),
    name='Redisautoqueryplan:Functional')
