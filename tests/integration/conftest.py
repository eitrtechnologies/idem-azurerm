import pytest
import random
import string
import asyncio


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def hub(hub):
    hub.pop.sub.add(dyne_name="acct")
    hub.pop.sub.add(dyne_name="exec")
    hub.pop.sub.load_subdirs(hub.exec, recurse=True)
    hub.pop.sub.add(dyne_name="states")
    hub.pop.sub.load_subdirs(hub.states, recurse=True)
    yield hub


@pytest.fixture(scope="session")
def acct_subs():
    yield ["azurerm"]


@pytest.fixture(scope="session")
def acct_profile():
    yield "default"


@pytest.fixture(scope="session")
def location():
    yield "eastus"


@pytest.fixture(scope="session")
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
def vm():
    yield "vm-idem-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(5)
    )


@pytest.fixture(scope="session")
def keyvault():
    yield "kv-idem-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )


@pytest.fixture(scope="session")
def storage_account():
    yield "stidem" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(16)
    )


@pytest.fixture(scope="session")
def storage_container():
    yield "container-idem-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(32)
    )


@pytest.fixture(scope="session")
def log_analytics_workspace():
    yield "log-idem-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(32)
    )


@pytest.fixture(scope="session")
def postgresql_server():
    yield "psql-server-idem-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )


@pytest.fixture(scope="session")
def vnet():
    yield "vnet-idem-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )


@pytest.fixture(scope="session")
def vnet2():
    yield "vnet-idem2-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )


@pytest.fixture(scope="session")
def subnet():
    yield "snet-idem-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )


@pytest.fixture(scope="session")
def public_ip_addr():
    yield "pip-idem-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )


@pytest.fixture(scope="session")
def public_ip_addr2():
    yield "pip-idem-2-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )


@pytest.fixture(scope="session")
def route_table():
    yield "rt-table-idem-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )


@pytest.fixture(scope="session")
def route():
    yield "rt-idem-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )


@pytest.fixture(scope="session")
def load_balancer():
    yield "lb-idem-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )


@pytest.fixture(scope="session")
def zone():
    yield "zone.idem." + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )


@pytest.fixture(scope="session")
def availability_set():
    yield "avail-idem-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )


@pytest.fixture(scope="session")
def network_interface():
    yield "nic-idem-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )


@pytest.fixture(scope="session")
def local_network_gateway():
    yield "lgw-idem-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )


@pytest.fixture(scope="session")
def ip_config():
    yield "ip-config-idem-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )


@pytest.fixture(scope="session")
def acr():
    yield "acrideminttest" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )
