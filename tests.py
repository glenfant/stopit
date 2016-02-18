# -*- coding: utf-8 -*-
import doctest
import os
import unittest

from stopit import ThreadingTimeout, threading_timeoutable, SignalTimeout, signal_timeoutable

# We run twice the same doctest with two distinct sets of globs
# This one is for testing signals based timeout control
signaling_globs = {
    'Timeout': SignalTimeout,
    'timeoutable': signal_timeoutable
}

# And this one is for testing threading based timeout control
threading_globs = {
    'Timeout': ThreadingTimeout,
    'timeoutable': threading_timeoutable
}


def suite():  # Func for setuptools.setup(test_suite=xxx)
    test_suite = unittest.TestSuite()
    test_suite.addTest(doctest.DocFileSuite('README.rst', globs=signaling_globs))
    if os.name == 'posix':  # Other OS have no support for signal.SIGALRM
        test_suite.addTest(doctest.DocFileSuite('README.rst', globs=threading_globs))
    return test_suite

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
