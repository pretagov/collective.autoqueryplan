# -*- coding: utf-8 -*-
import ast
import asyncore
import json
import os
import time
import socket
import StringIO
import posixpath
import logging
import threading

from App.config import getConfiguration
from Products.ZCatalog.plan import PriorityMap, Benchmark
from ZServer.ClockServer import LogHelper, ClockServer, timeslice
from ZServer.PubCore.ZEvent import Wakeup
from ZServer.medusa.http_server import http_request
from ZServer.medusa.default_handler import unquote
from ZServer.PubCore import handle
from ZServer.HTTPResponse import make_response
from ZPublisher.HTTPRequest import HTTPRequest
from zope.component import getUtility
from zope.component import ComponentLookupError
from zope.dottedname.resolve import resolve
from zope.interface import implements
from zope.publisher.browser import BrowserView

logger = logging.getLogger('collective.autoqueryplan')


def get_plan_path():
    path = os.environ.get('AUTOQUERYPLAN', None)
    if path is None:
        path = getConfiguration().clienthome
        path = os.path.join(path, 'queryplan.json')
    return path


def dump_pmap(obj, is_key=False):
    """
    Can't have sets, classes or complex objects as dict keys in json.

    Handle complex keys
    >>> dump_pmap({frozenset([1,2,3]):"blah"})
    {'{1, 2, 3}': 'blah'}

    >>> dump_pmap({(1,2,3):set(['a'])})
    {'(1, 2, 3)': "{'a'}"}

    Handles tuples as keys (which json can't)
    #TODO: it always assumes sets are frozen sets
    >>> load_pmap(dump_pmap({(1,2,3):set(['a'])}))
    {(1, 2, 3): frozenset(['a'])}

    Works for lists of sets in (even if not needed for this usecase
    >>> dump_pmap([1,2,set(['a'])])
    [1, 2, "{'a'}"]

    >>> load_pmap(dump_pmap([1,2,set(['a'])]))
    [1, 2, frozenset(['a'])]

    """
    if isinstance(obj, Benchmark):
        return (round(obj[0], 4),) + obj[1:]
    elif isinstance(obj, (frozenset, set)):
        return "{%s}" % str(list(obj))[1:-1]
    elif is_key and isinstance(obj, (list, tuple)):
        return str(obj)
    elif isinstance(obj, (tuple)):
        return (dump_pmap(i) for i in obj)
    elif isinstance(obj, (list)):
        return [dump_pmap(i) for i in obj]
    elif isinstance(obj, dict):
        return {dump_pmap(key, True): dump_pmap(value) for key, value in obj.items()}
    else:
        return obj

def load_pmap(obj):
    """ turn complex dict keys from strings back to types """
    if isinstance(obj, basestring):
        if obj.startswith('{'):
            return frozenset(ast.literal_eval("[%s]" % obj[1:-1]))
        elif obj.startswith('frozenset(['):
            return frozenset(ast.literal_eval(obj[len('frozenset('):-1]))
        elif obj.startswith('(') or obj.startswith('['):
            return ast.literal_eval(obj)
        else:
            return obj
    elif isinstance(obj, (tuple)):
        return (load_pmap(i) for i in obj)
    elif isinstance(obj, (list)):
        return [load_pmap(i) for i in obj]
    elif isinstance(obj, dict):
        return {load_pmap(key): load_pmap(value) for key, value in obj.items()}
    else:
        return obj


_load_default = PriorityMap.load_default

def load_dumped_plan(cls):
    path = get_plan_path()
    plan = None
    try:
        with open(path) as f:
            plan = f.read()
    except:
        logger.error("Problem reading queryplan %s" % path)
    if plan is not None:
        try:
            pmap = json.loads(plan)
            pmap = load_pmap(pmap)
            cls.load_pmap(path, pmap)
            return
        except Exception:
            #TODO: should put more sepecifc exceptions
            logger.error("Problem loading queryplan %s" % path)
    return _load_default(cls)

# Monkey patch querymap loading so we load autoqueryplan first
PriorityMap.load_default = classmethod(load_dumped_plan)


class DumpPlanView(BrowserView):
    def __call__(self):
        pmap = PriorityMap.get_value()
        pmap = dump_pmap(pmap)
        json_pmap = json.dumps(pmap, skipkeys=False, sort_keys=True, indent=4)
        with open(get_plan_path(),'w') as f:
            f.write(json_pmap)
        logger.info("Succesfully dumped queryplan to %s" % get_plan_path())
        return "Query plan dumped"

#
# class QueryPlanServer(ClockServer):
#     """ every hour dump a json version of the queryplan to disk """
#
#     pass
#
# class ClockServer(asyncore.dispatcher):
#     # prototype request environment
#     _ENV = dict(REQUEST_METHOD = 'GET',
#                 SERVER_PORT = 'Clock',
#                 SERVER_NAME = 'Zope Clock Server',
#                 SERVER_SOFTWARE = 'Zope',
#                 SERVER_PROTOCOL = 'HTTP/1.0',
#                 SCRIPT_NAME = '',
#                 GATEWAY_INTERFACE='CGI/1.1',
#                 REMOTE_ADDR = '0')
#
#     # required by ZServer
#     SERVER_IDENT = 'Zope Clock'
#
#     def __init__ (self, period=60, logger=None, handler=None):
#         self.period = period
#
#         self.last_slice = timeslice(period)
#
#
#         asyncore.dispatcher.__init__(self)
#         self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
#         self.logger = LogHelper(logger)
#         self.log_info('Clock server for auoqueryplan started (period: %s)'
#                       % (self.period))
#         if handler is None:
#             # for unit testing
#             handler = handle
#         self.zhandler = handler
#
#
#     def readable(self):
#         # generate a request at most once every self.period seconds
#         slice = timeslice(self.period)
#         if slice != self.last_slice:
#             # no need for threadsafety here, as we're only ever in one thread
#             self.last_slice = slice
#             req, zreq, resp = self.get_requests_and_response()
#             self.zhandler('Zope2', zreq, resp)
#         return False
#
#     def handle_read(self):
#         return True
#
#     def handle_write (self):
#         self.log_info('unexpected write event', 'warning')
#         return True
#
#     def writable(self):
#         return False
#
#     def handle_error (self):      # don't close the socket on error
#         (file,fun,line), t, v, tbinfo = asyncore.compact_traceback()
#         self.log_info('Problem in Clock (%s:%s %s)' % (t, v, tbinfo),
#                       'error')
#
