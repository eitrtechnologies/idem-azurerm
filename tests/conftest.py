# -*- coding: utf-8 -*-

# Import python libs
import os
import sys
import logging

CODE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
TPATH_DIR = os.path.join(os.path.dirname(__file__), "tpath")

if CODE_DIR in sys.path:
    sys.path.remove(CODE_DIR)
sys.path.insert(0, CODE_DIR)
sys.path.insert(0, TPATH_DIR)

# Import 3rd-party libs
import pytest


log = logging.getLogger("pop.tests")


def pytest_runtest_protocol(item, nextitem):
    """
    implements the runtest_setup/call/teardown protocol for
    the given test item, including capturing exceptions and calling
    reporting hooks.
    """
    log.debug(">>>>> START >>>>> {0}".format(item.name))


def pytest_runtest_teardown(item):
    """
    called after ``pytest_runtest_call``
    """
    log.debug("<<<<< END <<<<<<< {0}".format(item.name))


def pytest_configure(config):
    config.addinivalue_line("markers", "first: mark test to run first")
    config.addinivalue_line("markers", "second: mark test to run second")
    config.addinivalue_line(
        "markers", "second_to_last: mark test to run second to last"
    )
    config.addinivalue_line("markers", "last: mark test to run last")
    config.addinivalue_line(
        "markers", "slow: mark tests with an above average run time"
    )


@pytest.fixture
def os_sleep_secs():
    if "CI_RUN" in os.environ:
        return 1.75
    return 0.5
