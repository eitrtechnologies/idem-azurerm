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
    yield "idem-rg-inttest-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(20)
    )


@pytest.fixture(scope="session")
def keyvault():
    yield "idem-kv-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )


@pytest.fixture(scope="session")
def test_keyvault():
    yield "idem-test-kv-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )


@pytest.fixture(scope="session")
def test_key():
    yield "idem-test-key-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )


@pytest.fixture(scope="session")
def key():
    yield "idem-key-" + "".join(
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
def vnet2():
    yield "idem-vnet2-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )


@pytest.fixture(scope="session")
def subnet():
    yield "idem-subnet-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )


@pytest.fixture(scope="session")
def test_vnet():
    yield "idem-test-vnet-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )


@pytest.fixture(scope="session")
def test_subnet():
    yield "idem-test-subnet-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )


@pytest.fixture(scope="session")
def public_ip_addr():
    yield "idem-public-ip-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )


@pytest.fixture(scope="session")
def test_public_ip_addr():
    yield "idem-test-public-ip-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )


@pytest.fixture(scope="session")
def route_table():
    yield "idem-rt-table-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )


@pytest.fixture(scope="session")
def route():
    yield "idem-rt-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )


@pytest.fixture(scope="session")
def load_balancer():
    yield "idem-load-bal-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )


@pytest.fixture(scope="session")
def nsg():
    yield "idem-nsg-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )


@pytest.fixture(scope="session")
def zone():
    yield "idem.zone." + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )


@pytest.fixture(scope="session")
def availability_set():
    yield "idem-avail-set-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )


@pytest.fixture(scope="session")
def network_interface():
    yield "idem-net-iface-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )


@pytest.fixture(scope="session")
def test_network_interface():
    yield "idem-test-net-iface-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )
