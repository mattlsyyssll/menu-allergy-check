#!/usr/bin/env python3
"""Run the kit tests with no model and no network.   /usr/bin/python3 -I tests/run_tests.py   (from the kit folder or anywhere)"""
import os
import sys
import unittest

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'scripts', 'testkit'))

if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromName('test_kit')
    res = unittest.TextTestRunner(verbosity=1).run(suite)
    print('KIT TESTS %s (%d run, %d failed, %d errors, %d skipped)' % ('PASS' if res.wasSuccessful() else 'FAIL', res.testsRun, len(res.failures), len(res.errors), len(res.skipped)))
    sys.exit(0 if res.wasSuccessful() else 1)
