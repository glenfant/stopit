# -*- coding: utf-8 -*-
import doctest

def suite():  # Func for setuptools.setup(test_suite=xxx)
    suite = doctest.DocFileSuite('README.rst')
    return suite

if __name__ == '__main__':
    doctest.testfile('README.rst')
