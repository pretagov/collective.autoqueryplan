# -*- coding: utf-8 -*-
import doctest





def test_suite():
    suite = doctest.DocTestSuite('collective.autoqueryplan.server')
    return suite
