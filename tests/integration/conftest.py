import pop.hub
import pytest


@pytest.fixture(scope="session")
def hub():
    hub = pop.hub.Hub()
    for dyne in ("exec", "states"):
        hub.pop.sub.add(dyne_name=dyne)
    return hub
