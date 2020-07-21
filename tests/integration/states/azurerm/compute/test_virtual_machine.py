import pytest
import random
import string


@pytest.fixture(scope="module")
def password():
    yield "#" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(16)
    ) + "!"


"""
Ensure virtual machine exists:
  azurerm.compute.virtual_machine.present:
    - name: 'vm-test'
    - resource_group: 'rg-tests'
    - vm_size: 'Standard_B4ms'
    - image: 'MicrosoftWindowsServer|WindowsServer|2019-Datacenter|latest'
    - os_disk_size_gb: 120
    - virtual_network: 'eitrvnet'
    - subnet: 'default'
    - admin_password: 'Password321$$'
"""


@pytest.fixture(scope="module")
def vm_size():
    yield "Standard_B4ms"


@pytest.fixture(scope="module")
def linux_image():
    yield "OpenLogic|CentOS|7.7|latest"


@pytest.fixture(scope="module")
def windows_image():
    yield "OpenLogic|CentOS|7.7|latest"


@pytest.mark.run(order=5)
@pytest.mark.asyncio
async def test_present(
    hub, ctx, vm, resource_group, vm_size, windows_image, vnet, subnet, password
):
    expected = {
        "changes": {"new": {"name": vm,}, "old": {},},
        "comment": f"Virtual machine {vm} has been created.",
        "name": vm,
        "result": True,
    }
    ret = await hub.states.azurerm.compute.virtual_machine.present(
        ctx,
        name=vm,
        resource_group=resource_group,
        vm_size=vm_size,
        image=windows_image,
        os_disk_size_gb=128,
        virtual_network=vnet,
        subnet=subnet,
        admin_password=password,
    )
    assert ret == expected


@pytest.mark.skip(reason="not yet")
@pytest.mark.run(order=5, after="test_present", before="test_absent")
@pytest.mark.asyncio
async def test_changes(hub, ctx, availability_set, resource_group, tags):
    expected = {
        "changes": {"tags": {"new": tags}},
        "comment": f"Availability set {availability_set} has been updated.",
        "name": availability_set,
        "result": True,
    }
    ret = await hub.states.azurerm.compute.availability_set.present(
        ctx, name=availability_set, resource_group=resource_group, tags=tags
    )
    assert ret == expected


@pytest.mark.skip(reason="not yet")
@pytest.mark.run(order=-5)
@pytest.mark.asyncio
async def test_absent(hub, ctx, availability_set, resource_group):
    expected = {
        "changes": {"new": {}, "old": {"name": availability_set,},},
        "comment": f"Availability set {availability_set} has been deleted.",
        "name": availability_set,
        "result": True,
    }
    ret = await hub.states.azurerm.compute.availability_set.absent(
        ctx, availability_set, resource_group
    )
    assert ret["changes"]["new"] == expected["changes"]["new"]
    assert ret["changes"]["old"]["name"] == expected["changes"]["old"]["name"]
    assert ret["result"] == expected["result"]
