import pytest
import random
import string


@pytest.fixture
def hub(hub):
    hub.pop.sub.add(dyne_name="exec")
    hub.pop.sub.load_subdirs(hub.exec, recurse=True)
    hub.pop.sub.add(dyne_name="states")
    hub.pop.sub.load_subdirs(hub.states, recurse=True)
    yield hub


@pytest.fixture
def acct_subs():
    yield ["azurerm"]


@pytest.fixture
def acct_profile():
    yield "default"


@pytest.fixture
def location():
    yield "eastus"


@pytest.fixture
def resource_group():
    yield "rg-idem-inttest"
