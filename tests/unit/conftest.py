import pop.hub
import pytest


@pytest.fixture(scope="session")
def hub():
    hub = pop.hub.Hub()
    for dyne in ("exec", "states"):
        hub.pop.sub.add(dyne_name=dyne)
    yield hub


@pytest.fixture(scope="function")
def mock_hub(hub):
    """
    A hub specific to corn unit testing
    """
    mock_hub = hub.pop.testing.mock_hub()
    # TODO replace mocked functions with necessary real ones
    # mock_hub.pop.data.imap = hub.pop.data.imap
    # mock_hub.exec.utils = hub.exec.utils
    yield mock_hub
