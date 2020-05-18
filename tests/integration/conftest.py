import pop.hub
import pytest


@pytest.fixture(scope="session")
def hub():
    hub = pop.hub.Hub()
    hub.pop.sub.add(dyne_name="acct")
    hub.pop.sub.add(dyne_name="exec")
    hub.pop.sub.load_subdirs(hub.exec, recurse=True)
    hub.pop.sub.add(dyne_name="states")
    hub.pop.sub.load_subdirs(hub.states, recurse=True)
    return hub
