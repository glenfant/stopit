# -*- coding: utf-8 -*-
import doctest
import unittest

from stopit import ThreadingTimeout, threading_timeoutable, SignalTimeout, signal_timeoutable

threading_globs = {
    'Timeout': ThreadingTimeout,
    'timeoutable': threading_timeoutable
}

signaling_globs = {
    'Timeout': SignalTimeout,
    'timeoutable': signal_timeoutable
}


def suite():  # Func for setuptools.setup(test_suite=xxx)
    test_suite = unittest.TestSuite()
    test_suite.addTest(doctest.DocFileSuite('README.rst', globs=threading_globs))
    test_suite.addTest(doctest.DocFileSuite('README.rst', globs=signaling_globs))
    return test_suite

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
