import pytest
import random
import string


@pytest.fixture
def hub(hub):
    hub.pop.sub.add(dyne_name="acct")
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
def tags():
    yield {
        "Organization": "Everest",
        "Owner": "Elmer Fudd Gantry",
    }


@pytest.fixture(scope="session")
def resource_group():
    yield "rg-idem-inttest-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(20)
    )


@pytest.fixture(scope="session")
def keyvault():
    yield "kv-idem-inttest-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )


@pytest.fixture(scope="session")
def storage_account():
    yield "idemacc" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(16)
    )


@pytest.fixture(scope="session")
def storage_container():
    yield "idem-container" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(32)
    )


@pytest.fixture(scope="session")
def log_analytics_workspace():
    yield "idem-law-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(32)
    )


@pytest.fixture(scope="session")
def postgresql_server():
    yield "idem-psql-server-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )


@pytest.fixture(scope="session")
def vnet():
    yield "idem-vnet-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )


@pytest.fixture(scope="session")
def subnet():
    yield "idem-subnet-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )


@pytest.fixture(scope="session")
def public_ip_addr():
    yield "idem-public-ip-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )
